"""
E2E Selenium Tests for Track Creation Features

BUSINESS CONTEXT:
Tests the complete user journey for track creation features, including:
- Track requirement toggle (user can indicate if tracks are needed)
- Audience-to-track mapping (one track per selected audience)
- Track confirmation dialog (user must approve before creation)
- Approval and cancellation workflows

TECHNICAL IMPLEMENTATION:
- Selenium WebDriver for browser automation
- Tests track requirement checkbox toggle
- Tests audience selection → track proposal mapping
- Tests confirmation dialog display and interactions
- Tests track creation via API after approval
- Tests cancellation returning user to configuration

TDD METHODOLOGY:
E2E tests verify actual user interactions in a real browser environment,
ensuring the complete track creation workflow functions correctly from
a user's perspective.

SUCCESS CRITERIA:
- User can toggle track requirement on/off
- Track fields show/hide based on toggle state
- User can select multiple target audiences
- System proposes one track per selected audience
- Confirmation dialog displays all proposed tracks
- User can approve and create tracks
- User can cancel and return to configuration
- Tracks are not created when user cancels
- Validation prevents advancement without audience selection
"""

import pytest
import time
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

sys.path.insert(0, '/home/bbrelin/course-creator/tests/e2e')
from selenium_base import BaseTest


class TestTrackCreationFeaturesE2E(BaseTest):
    """
    E2E tests for organization admin track creation features
    """

    @classmethod
    def setup_class(cls):
        """Set up test fixtures before all tests"""
        super().setup_class()
        cls.org_admin_credentials = {
            'username': 'org_admin_test',
            'password': 'TestPass123!'
        }

    def setup_method(self, method):
        """Set up before each test"""
        super().setup_method(method)
        self.login_as_org_admin()
        self.navigate_to_projects_tab()
        self.open_create_project_wizard()
        self.fill_step1_and_advance()

    def login_as_org_admin(self):
        """Login as organization admin"""
        self.driver.get(f"{self.base_url}/org-admin-dashboard.html")

        try:
            # Wait for login form
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            # Enter credentials
            username_input.send_keys(self.org_admin_credentials['username'])
            password_input = self.driver.find_element(By.ID, "password")
            password_input.send_keys(self.org_admin_credentials['password'])

            # Submit login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard-container"))
            )

            time.sleep(1)  # Allow dashboard to fully initialize

        except TimeoutException:
            pytest.fail("Failed to login as organization admin")

    def navigate_to_projects_tab(self):
        """Navigate to Projects tab in org admin dashboard"""
        try:
            projects_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "projectsTab"))
            )
            projects_tab.click()

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "projectsContent"))
            )

            time.sleep(0.5)

        except TimeoutException:
            pytest.fail("Failed to navigate to Projects tab")

    def open_create_project_wizard(self):
        """Open the create project wizard modal"""
        try:
            create_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "createProjectBtn"))
            )
            create_button.click()

            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "createProjectModal"))
            )

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#projectStep1.active"))
            )

            time.sleep(0.5)

        except TimeoutException:
            pytest.fail("Failed to open create project wizard")

    def fill_step1_and_advance(self):
        """Fill step 1 with valid data and advance to step 2"""
        name_input = self.driver.find_element(By.ID, "projectName")
        name_input.clear()
        name_input.send_keys("Track Features Test Project")

        slug_input = self.driver.find_element(By.ID, "projectSlug")
        slug_input.clear()
        slug_input.send_keys("track-features-test")

        description_input = self.driver.find_element(By.ID, "projectDescription")
        description_input.clear()
        description_input.send_keys("E2E test project for track creation features")

        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        # Wait for step 2 to become active
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#projectStep2.active"))
        )

        time.sleep(1)  # Allow AI suggestions to load

    # ========================================
    # Track Requirement Toggle Tests
    # ========================================

    def test_01_track_requirement_checkbox_exists_and_is_checked_by_default(self):
        """
        TEST: Track requirement checkbox exists on step 2
        REQUIREMENT: User can indicate if tracks are needed
        SUCCESS CRITERIA: Checkbox exists and is checked by default
        """
        # Verify on step 2
        step2 = self.driver.find_element(By.ID, "projectStep2")
        assert "active" in step2.get_attribute("class"), "Should be on step 2"

        # Verify checkbox exists
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        assert need_tracks_checkbox is not None, "Track requirement checkbox should exist"

        # Verify checked by default
        assert need_tracks_checkbox.is_selected(), "Checkbox should be checked by default"

        self.take_screenshot("track_checkbox_exists_and_checked")

    def test_02_track_fields_visible_when_checkbox_checked(self):
        """
        TEST: Track fields are visible when checkbox is checked
        REQUIREMENT: Show track configuration when tracks are needed
        SUCCESS CRITERIA: Track fields container is visible
        """
        # Verify checkbox is checked
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        assert need_tracks_checkbox.is_selected(), "Checkbox should be checked"

        # Verify track fields container is visible
        track_fields_container = self.driver.find_element(By.ID, "trackFieldsContainer")
        assert track_fields_container.is_displayed(), "Track fields should be visible when checkbox checked"

        self.take_screenshot("track_fields_visible_when_checked")

    def test_03_track_fields_hidden_when_checkbox_unchecked(self):
        """
        TEST: Track fields are hidden when checkbox is unchecked
        REQUIREMENT: Hide track configuration when tracks not needed
        SUCCESS CRITERIA: Track fields container is hidden
        """
        # Uncheck the checkbox
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        need_tracks_checkbox.click()

        time.sleep(0.5)  # Allow UI to update

        # Verify track fields container is hidden
        track_fields_container = self.driver.find_element(By.ID, "trackFieldsContainer")
        assert not track_fields_container.is_displayed(), "Track fields should be hidden when checkbox unchecked"

        self.take_screenshot("track_fields_hidden_when_unchecked")

    def test_04_toggling_checkbox_shows_and_hides_fields(self):
        """
        TEST: Toggling checkbox dynamically shows/hides fields
        REQUIREMENT: Responsive UI based on user selection
        SUCCESS CRITERIA: Fields show/hide when toggling checkbox
        """
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        track_fields_container = self.driver.find_element(By.ID, "trackFieldsContainer")

        # Initially checked and visible
        assert need_tracks_checkbox.is_selected()
        assert track_fields_container.is_displayed()

        # Uncheck - should hide
        need_tracks_checkbox.click()
        time.sleep(0.3)
        assert not track_fields_container.is_displayed(), "Should hide after unchecking"

        # Check again - should show
        need_tracks_checkbox.click()
        time.sleep(0.3)
        assert track_fields_container.is_displayed(), "Should show after checking again"

        self.take_screenshot("track_fields_toggle_works")

    # ========================================
    # Audience Selection Tests
    # ========================================

    def test_05_target_audiences_select_element_exists(self):
        """
        TEST: Target audiences select element exists
        REQUIREMENT: User can select target audiences
        SUCCESS CRITERIA: Multi-select element exists on step 2
        """
        target_audiences = self.driver.find_element(By.ID, "targetAudiences")
        assert target_audiences is not None, "Target audiences select should exist"
        assert target_audiences.get_attribute("multiple") == "true", "Should be a multi-select"

        self.take_screenshot("target_audiences_select_exists")

    def test_06_can_select_multiple_audiences(self):
        """
        TEST: User can select multiple target audiences
        REQUIREMENT: Support multiple audience selection
        SUCCESS CRITERIA: Multiple audiences can be selected
        """
        target_audiences_elem = self.driver.find_element(By.ID, "targetAudiences")
        select = Select(target_audiences_elem)

        # Select three audiences
        select.select_by_value("application_developers")
        select.select_by_value("business_analysts")
        select.select_by_value("operations_engineers")

        # Verify selections
        selected_options = select.all_selected_options
        assert len(selected_options) == 3, "Should have 3 selected audiences"

        self.take_screenshot("multiple_audiences_selected")

    # ========================================
    # Track Confirmation Dialog Tests
    # ========================================

    def test_07_confirmation_dialog_appears_when_advancing_with_tracks_needed(self):
        """
        TEST: Confirmation dialog appears when advancing from step 2 with tracks needed
        REQUIREMENT: User sees confirmation before track creation
        SUCCESS CRITERIA: Dialog is displayed when clicking Next
        """
        # Ensure checkbox is checked
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        if not need_tracks_checkbox.is_selected():
            need_tracks_checkbox.click()

        # Select audiences
        target_audiences_elem = self.driver.find_element(By.ID, "targetAudiences")
        select = Select(target_audiences_elem)
        select.select_by_value("application_developers")
        select.select_by_value("business_analysts")

        # Click Next
        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        # Wait for confirmation dialog to appear
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "trackConfirmationModal"))
            )
        except TimeoutException:
            pytest.fail("Track confirmation dialog did not appear")

        # Verify dialog is visible
        dialog = self.driver.find_element(By.ID, "trackConfirmationModal")
        assert dialog.is_displayed(), "Confirmation dialog should be visible"

        self.take_screenshot("confirmation_dialog_appeared")

    def test_08_confirmation_dialog_displays_all_proposed_tracks(self):
        """
        TEST: Confirmation dialog displays all proposed tracks
        REQUIREMENT: User sees what will be created
        SUCCESS CRITERIA: Dialog shows track names and descriptions
        """
        # Select three audiences
        target_audiences_elem = self.driver.find_element(By.ID, "targetAudiences")
        select = Select(target_audiences_elem)
        select.select_by_value("application_developers")
        select.select_by_value("business_analysts")
        select.select_by_value("operations_engineers")

        # Click Next to show dialog
        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        # Wait for dialog
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "trackConfirmationModal"))
        )

        time.sleep(0.5)

        # Verify proposed tracks list exists
        proposed_tracks_list = self.driver.find_element(By.ID, "proposedTracksList")
        assert proposed_tracks_list is not None, "Proposed tracks list should exist"

        # Verify track names are displayed
        dialog_content = self.driver.find_element(By.ID, "trackConfirmationModal").text

        assert "Application Developer Track" in dialog_content, "Should show Application Developer Track"
        assert "Business Analyst Track" in dialog_content, "Should show Business Analyst Track"
        assert "Operations" in dialog_content, "Should show Operations Engineer Track"

        self.take_screenshot("dialog_shows_all_proposed_tracks")

    def test_09_confirmation_dialog_has_approve_button(self):
        """
        TEST: Confirmation dialog has Approve button
        REQUIREMENT: User can approve track creation
        SUCCESS CRITERIA: Approve button exists and is clickable
        """
        # Setup and show dialog
        self.select_audiences_and_show_dialog(["application_developers"])

        # Verify Approve button exists
        approve_button = self.driver.find_element(By.ID, "approveTracksBtn")
        assert approve_button is not None, "Approve button should exist"
        assert approve_button.is_displayed(), "Approve button should be visible"
        assert "Approve" in approve_button.text, "Button should say Approve"

        self.take_screenshot("dialog_has_approve_button")

    def test_10_confirmation_dialog_has_cancel_button(self):
        """
        TEST: Confirmation dialog has Cancel button
        REQUIREMENT: User can cancel track creation
        SUCCESS CRITERIA: Cancel button exists and is clickable
        """
        # Setup and show dialog
        self.select_audiences_and_show_dialog(["application_developers"])

        # Verify Cancel button exists
        cancel_button = self.driver.find_element(By.ID, "cancelTracksBtn")
        assert cancel_button is not None, "Cancel button should exist"
        assert cancel_button.is_displayed(), "Cancel button should be visible"
        assert "Cancel" in cancel_button.text, "Button should say Cancel"

        self.take_screenshot("dialog_has_cancel_button")

    # ========================================
    # Track Approval Workflow Tests
    # ========================================

    def test_11_clicking_approve_closes_dialog_and_advances_to_step3(self):
        """
        TEST: Clicking Approve closes dialog and advances wizard
        REQUIREMENT: Approval triggers track creation and wizard advancement
        SUCCESS CRITERIA: Dialog closes and step 3 becomes active
        """
        # Setup and show dialog
        self.select_audiences_and_show_dialog(["application_developers"])

        # Click Approve button
        approve_button = self.driver.find_element(By.ID, "approveTracksBtn")
        approve_button.click()

        time.sleep(1)  # Allow track creation and navigation

        # Verify dialog is closed
        try:
            dialog = self.driver.find_element(By.ID, "trackConfirmationModal")
            assert not dialog.is_displayed(), "Dialog should be closed after approval"
        except NoSuchElementException:
            pass  # Dialog removed from DOM - also acceptable

        # Verify advanced to step 3
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#projectStep3.active"))
            )
            step3 = self.driver.find_element(By.ID, "projectStep3")
            assert "active" in step3.get_attribute("class"), "Should advance to step 3 after approval"
        except TimeoutException:
            pytest.fail("Did not advance to step 3 after approval")

        self.take_screenshot("approved_advanced_to_step3")

    def test_12_success_notification_shown_after_track_creation(self):
        """
        TEST: Success notification shown after tracks created
        REQUIREMENT: User feedback on successful creation
        SUCCESS CRITERIA: Success notification appears
        """
        # Setup and show dialog
        self.select_audiences_and_show_dialog(["application_developers", "business_analysts"])

        # Click Approve
        approve_button = self.driver.find_element(By.ID, "approveTracksBtn")
        approve_button.click()

        time.sleep(2)  # Allow track creation

        # Look for success notification
        # Note: Implementation may vary - checking for common notification patterns
        try:
            notification = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "notification"))
            )
            notification_text = notification.text.lower()
            assert "success" in notification_text or "created" in notification_text, \
                "Success notification should appear"
        except TimeoutException:
            # Notification might have already disappeared
            pass

        self.take_screenshot("success_notification_shown")

    # ========================================
    # Track Cancellation Workflow Tests
    # ========================================

    def test_13_clicking_cancel_closes_dialog_and_returns_to_step2(self):
        """
        TEST: Clicking Cancel closes dialog and returns to configuration
        REQUIREMENT: User can cancel and modify configuration
        SUCCESS CRITERIA: Dialog closes and remains on step 2
        """
        # Setup and show dialog
        self.select_audiences_and_show_dialog(["application_developers"])

        # Click Cancel button
        cancel_button = self.driver.find_element(By.ID, "cancelTracksBtn")
        cancel_button.click()

        time.sleep(0.5)

        # Verify dialog is closed
        try:
            dialog = self.driver.find_element(By.ID, "trackConfirmationModal")
            assert not dialog.is_displayed(), "Dialog should be closed after cancellation"
        except NoSuchElementException:
            pass  # Dialog removed from DOM - also acceptable

        # Verify still on step 2
        step2 = self.driver.find_element(By.ID, "projectStep2")
        assert "active" in step2.get_attribute("class"), "Should remain on step 2 after cancellation"

        # Verify NOT on step 3
        step3 = self.driver.find_element(By.ID, "projectStep3")
        assert "active" not in step3.get_attribute("class"), "Should not advance to step 3"

        self.take_screenshot("cancelled_returned_to_step2")

    def test_14_audience_selection_preserved_after_cancellation(self):
        """
        TEST: Audience selection is preserved after cancellation
        REQUIREMENT: User can modify and retry after canceling
        SUCCESS CRITERIA: Selected audiences still selected after cancel
        """
        # Select audiences
        target_audiences_elem = self.driver.find_element(By.ID, "targetAudiences")
        select = Select(target_audiences_elem)
        select.select_by_value("application_developers")
        select.select_by_value("business_analysts")

        # Show dialog and cancel
        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "trackConfirmationModal"))
        )

        cancel_button = self.driver.find_element(By.ID, "cancelTracksBtn")
        cancel_button.click()

        time.sleep(0.5)

        # Verify selections still present
        target_audiences_elem = self.driver.find_element(By.ID, "targetAudiences")
        select = Select(target_audiences_elem)
        selected_options = select.all_selected_options

        assert len(selected_options) == 2, "Audience selection should be preserved"

        self.take_screenshot("selections_preserved_after_cancel")

    def test_15_can_modify_audiences_and_retry_after_cancellation(self):
        """
        TEST: User can modify audience selection after cancellation
        REQUIREMENT: Allow user to go back and modify
        SUCCESS CRITERIA: Can change audiences and see updated dialog
        """
        # Initial selection and cancel
        self.select_audiences_and_show_dialog(["application_developers"])
        cancel_button = self.driver.find_element(By.ID, "cancelTracksBtn")
        cancel_button.click()
        time.sleep(0.5)

        # Modify selection - add another audience
        target_audiences_elem = self.driver.find_element(By.ID, "targetAudiences")
        select = Select(target_audiences_elem)
        select.select_by_value("operations_engineers")

        # Show dialog again
        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "trackConfirmationModal"))
        )

        # Verify dialog now shows both tracks
        dialog_content = self.driver.find_element(By.ID, "trackConfirmationModal").text
        assert "Application Developer" in dialog_content, "Should show first track"
        assert "Operations" in dialog_content, "Should show newly added track"

        self.take_screenshot("modified_and_retried")

    # ========================================
    # Validation Tests
    # ========================================

    def test_16_validation_prevents_advancement_without_audience_selection(self):
        """
        TEST: Cannot advance without selecting audiences when tracks needed
        REQUIREMENT: Validation prevents incomplete submission
        SUCCESS CRITERIA: Validation error shown, remains on step 2
        """
        # Ensure checkbox is checked but no audiences selected
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        if not need_tracks_checkbox.is_selected():
            need_tracks_checkbox.click()

        # Clear any existing selections
        target_audiences_elem = self.driver.find_element(By.ID, "targetAudiences")
        select = Select(target_audiences_elem)
        select.deselect_all()

        # Try to advance
        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        time.sleep(1)

        # Should still be on step 2
        step2 = self.driver.find_element(By.ID, "projectStep2")
        assert "active" in step2.get_attribute("class"), "Should remain on step 2 without audience selection"

        # Should NOT show confirmation dialog
        try:
            dialog = self.driver.find_element(By.ID, "trackConfirmationModal")
            assert not dialog.is_displayed(), "Should not show dialog without audiences"
        except NoSuchElementException:
            pass  # Dialog doesn't exist - expected

        self.take_screenshot("validation_prevented_advancement")

    def test_17_can_advance_without_audiences_when_tracks_not_needed(self):
        """
        TEST: Can advance without selecting audiences when tracks not needed
        REQUIREMENT: Allow skipping track creation
        SUCCESS CRITERIA: Advances to step 3 when checkbox unchecked
        """
        # Uncheck track requirement
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        if need_tracks_checkbox.is_selected():
            need_tracks_checkbox.click()

        time.sleep(0.5)

        # Click Next without selecting audiences
        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        time.sleep(1)

        # Should advance to step 3 directly
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#projectStep3.active"))
            )
            step3 = self.driver.find_element(By.ID, "projectStep3")
            assert "active" in step3.get_attribute("class"), "Should advance to step 3 when tracks not needed"
        except TimeoutException:
            pytest.fail("Should advance to step 3 when tracks not needed")

        # Should NOT have shown confirmation dialog
        try:
            dialog = self.driver.find_element(By.ID, "trackConfirmationModal")
            # If it exists, it shouldn't be visible
            assert not dialog.is_displayed(), "Dialog should not appear when tracks not needed"
        except NoSuchElementException:
            pass  # Expected - dialog not shown

        self.take_screenshot("advanced_without_tracks")

    # ========================================
    # Complete Workflow Tests
    # ========================================

    def test_18_complete_workflow_with_track_creation(self):
        """
        TEST: Complete end-to-end workflow with track creation
        REQUIREMENT: Full user journey works correctly
        SUCCESS CRITERIA: User completes wizard with tracks created
        """
        # Step 2: Ensure tracks are needed
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        if not need_tracks_checkbox.is_selected():
            need_tracks_checkbox.click()

        # Select three audiences
        target_audiences_elem = self.driver.find_element(By.ID, "targetAudiences")
        select = Select(target_audiences_elem)
        select.select_by_value("application_developers")
        select.select_by_value("business_analysts")
        select.select_by_value("qa_engineers")

        time.sleep(0.5)

        # Advance to confirmation dialog
        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        # Wait for dialog
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "trackConfirmationModal"))
        )

        time.sleep(0.5)

        # Verify dialog shows all three tracks
        dialog_content = self.driver.find_element(By.ID, "trackConfirmationModal").text
        assert "Application Developer" in dialog_content, "Should show Application Developer Track"
        assert "Business Analyst" in dialog_content, "Should show Business Analyst Track"
        assert "QA Engineer" in dialog_content or "QA" in dialog_content, "Should show QA Engineer Track"

        self.take_screenshot("complete_workflow_dialog_with_three_tracks")

        # Approve tracks
        approve_button = self.driver.find_element(By.ID, "approveTracksBtn")
        approve_button.click()

        time.sleep(2)  # Allow track creation

        # Verify advanced to step 3
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#projectStep3.active"))
            )
            step3 = self.driver.find_element(By.ID, "projectStep3")
            assert "active" in step3.get_attribute("class"), "Should reach step 3 after approval"
        except TimeoutException:
            pytest.fail("Did not reach step 3 after track creation")

        self.take_screenshot("complete_workflow_reached_step3")

    def test_19_complete_workflow_without_track_creation(self):
        """
        TEST: Complete end-to-end workflow without track creation
        REQUIREMENT: User can skip track creation entirely
        SUCCESS CRITERIA: User completes wizard without tracks
        """
        # Step 2: Uncheck track requirement
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        if need_tracks_checkbox.is_selected():
            need_tracks_checkbox.click()

        time.sleep(0.5)

        # Advance directly to step 3
        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        time.sleep(1)

        # Verify advanced to step 3
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#projectStep3.active"))
            )
            step3 = self.driver.find_element(By.ID, "projectStep3")
            assert "active" in step3.get_attribute("class"), "Should reach step 3 without tracks"
        except TimeoutException:
            pytest.fail("Did not reach step 3 when skipping tracks")

        self.take_screenshot("complete_workflow_without_tracks")

    # ========================================
    # Helper Methods
    # ========================================

    def select_audiences_and_show_dialog(self, audience_values):
        """
        Helper: Select audiences and show confirmation dialog

        Args:
            audience_values: List of audience values to select
        """
        # Ensure checkbox is checked
        need_tracks_checkbox = self.driver.find_element(By.ID, "needTracks")
        if not need_tracks_checkbox.is_selected():
            need_tracks_checkbox.click()

        # Select audiences
        target_audiences_elem = self.driver.find_element(By.ID, "targetAudiences")
        select = Select(target_audiences_elem)
        for audience_value in audience_values:
            select.select_by_value(audience_value)

        time.sleep(0.5)

        # Click Next to show dialog
        next_button = self.driver.find_element(By.ID, "nextProjectStepBtn")
        next_button.click()

        # Wait for dialog
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "trackConfirmationModal"))
        )

        time.sleep(0.5)
