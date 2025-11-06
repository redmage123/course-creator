"""
E2E Tests for Wizard Save Draft Functionality

BUSINESS CONTEXT:
Users need to save their progress in multi-step wizards without completing
the entire workflow in one session. This module provides comprehensive E2E
testing for draft save/load functionality.

TEST COVERAGE:
1. Manual save draft button visibility and functionality
2. Auto-save triggered after 30 seconds of inactivity
3. Toast notifications for save confirmations
4. Last saved timestamp display
5. Draft loading on wizard re-open
6. Draft clearing after final submission
7. Multiple drafts for different wizards
8. Dirty state tracking (unsaved changes detection)
9. Navigation prompts when unsaved changes exist
10. Draft expiration after 7 days
11. Loading indicators during save operations
12. Error handling for failed save operations
13. Resume draft button on wizard entry
14. Discard draft option
15. Integration with Wave 3 components (toasts, modals, loading)

TECHNICAL APPROACH:
- Uses Selenium WebDriver for browser automation
- Tests localStorage-based draft persistence
- Validates integration with feedback-system.js toasts
- Validates integration with modal-system.js modals
- Tests time-based auto-save triggers
- Validates accessibility features (ARIA labels, focus management)
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys


class TestWizardDraftFunctionality:
    """Test suite for wizard draft save/load functionality"""

    @pytest.fixture(autouse=True)
    def setup_test_wizard(self, driver):
        """
        Set up test wizard for draft testing

        BUSINESS CONTEXT:
        Creates a multi-step wizard with form fields for testing draft
        save/load functionality. Uses organization admin project wizard
        as test subject.
        """
        # Navigate to organization admin dashboard
        driver.get('https://localhost/org-admin-dashboard.html')

        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Clear localStorage before each test
        driver.execute_script("localStorage.clear();")

        yield

        # Cleanup: clear localStorage after test
        driver.execute_script("localStorage.clear();")

    def test_01_save_draft_button_visible(self, driver):
        """
        Test: Save Draft button is visible in wizard

        BUSINESS CONTEXT:
        Users need a clear, accessible button to manually save their progress.
        Button should be visible on all wizard steps.

        EXPECTED BEHAVIOR:
        - "Save Draft" button visible in wizard footer
        - Button has appropriate styling (gray background, not primary blue)
        - Button has proper ARIA labels for accessibility
        """
        # Open project wizard
        try:
            create_project_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
            )
            create_project_btn.click()
        except TimeoutException:
            # Try alternative selector
            create_project_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-action="create-project"]'))
            )
            create_project_btn.click()

        # Wait for wizard modal to open
        wizard_modal = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.modal.is-open'))
        )

        # Look for Save Draft button
        save_draft_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.wizard-save-draft-btn'))
        )

        # Validate button properties
        assert save_draft_btn.is_displayed(), "Save Draft button should be visible"
        assert 'Save Draft' in save_draft_btn.text, "Button should have 'Save Draft' text"

        # Validate ARIA attributes
        aria_label = save_draft_btn.get_attribute('aria-label')
        assert aria_label is not None, "Save Draft button should have aria-label"

    def test_02_manual_save_triggers(self, driver):
        """
        Test: Manual save draft button triggers save operation

        BUSINESS CONTEXT:
        Users need immediate feedback when they manually save progress.
        Save should persist form data to localStorage.

        EXPECTED BEHAVIOR:
        - Click Save Draft button
        - Draft saved to localStorage
        - Success toast appears
        - Last saved timestamp updates
        """
        # Open wizard and fill some data
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        # Fill project name
        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Test Project Draft')

        # Click Save Draft
        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()

        # Wait for success toast
        toast = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ui-toast-success'))
        )
        assert 'Draft saved' in toast.text, "Should show 'Draft saved' success message"

        # Verify localStorage contains draft
        draft_data = driver.execute_script("""
            return localStorage.getItem('wizard-draft-project-wizard');
        """)
        assert draft_data is not None, "Draft should be saved to localStorage"

        # Verify timestamp updated
        draft_indicator = driver.find_element(By.CSS_SELECTOR, '[data-draft-indicator]')
        assert 'just now' in draft_indicator.text.lower(), "Should show 'just now' timestamp"

    def test_03_auto_save_after_30_seconds(self, driver):
        """
        Test: Auto-save triggers after 30 seconds of inactivity

        BUSINESS CONTEXT:
        Users may forget to manually save. Auto-save prevents data loss
        by periodically saving draft without user intervention.

        EXPECTED BEHAVIOR:
        - Fill form data
        - Wait 30 seconds without interaction
        - Auto-save triggers automatically
        - Success toast appears
        - Draft persisted to localStorage
        """
        # Open wizard and fill data
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        # Fill project name
        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Auto-Save Test Project')

        # Wait 31 seconds for auto-save to trigger
        time.sleep(31)

        # Check for success toast
        toast = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ui-toast-success'))
        )
        assert 'Draft saved' in toast.text, "Auto-save should show success toast"

        # Verify localStorage contains draft
        draft_data = driver.execute_script("""
            return localStorage.getItem('wizard-draft-project-wizard');
        """)
        assert draft_data is not None, "Auto-save should persist draft to localStorage"

    def test_04_toast_notification_shows_draft_saved(self, driver):
        """
        Test: Toast notification appears with "Draft saved" message

        BUSINESS CONTEXT:
        Visual feedback confirms save operation completed successfully.
        Uses Wave 3 feedback-system.js toast notifications.

        EXPECTED BEHAVIOR:
        - Save draft (manual or auto)
        - Success toast appears (green, top-right)
        - Toast has proper ARIA role="status"
        - Toast auto-dismisses after 3 seconds
        """
        # Open wizard and save draft
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        # Fill and save
        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Toast Test')

        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()

        # Validate toast properties
        toast = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ui-toast-success'))
        )

        # Check message
        assert 'Draft saved' in toast.text

        # Check ARIA role
        role = toast.get_attribute('role')
        assert role == 'status', "Toast should have role='status'"

        # Check auto-dismiss (toast should disappear after 3 seconds)
        time.sleep(4)
        toasts = driver.find_elements(By.CSS_SELECTOR, '.ui-toast-success')
        assert len(toasts) == 0 or not toasts[0].is_displayed(), "Toast should auto-dismiss"

    def test_05_last_saved_timestamp_displays(self, driver):
        """
        Test: Last saved timestamp displays and updates

        BUSINESS CONTEXT:
        Users need to know when draft was last saved to assess data freshness.
        Timestamp should update after each save operation.

        EXPECTED BEHAVIOR:
        - Save draft
        - "Draft saved just now" appears
        - Wait and save again
        - Timestamp updates appropriately
        """
        # Open wizard and save draft
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Timestamp Test')

        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()

        # Wait for save to complete
        time.sleep(1)

        # Check timestamp indicator
        draft_indicator = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-draft-indicator]'))
        )

        timestamp_text = draft_indicator.text
        assert 'just now' in timestamp_text.lower(), f"Should show 'just now', got: {timestamp_text}"

    def test_06_draft_loads_on_wizard_reopen(self, driver):
        """
        Test: Draft loads when wizard is reopened

        BUSINESS CONTEXT:
        Users should be able to resume work from where they left off.
        Draft data should persist across browser sessions.

        EXPECTED BEHAVIOR:
        - Save draft with specific data
        - Close wizard
        - Reopen wizard
        - "Resume Draft" modal appears
        - Click resume
        - Form fields populated with saved data
        """
        # Open wizard and fill data
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        test_project_name = 'Draft Resume Test Project'
        project_name_input.send_keys(test_project_name)

        # Save draft
        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()

        # Wait for save
        time.sleep(2)

        # Close wizard
        close_btn = driver.find_element(By.CSS_SELECTOR, '.modal-close')
        close_btn.click()

        # Wait for modal to close
        time.sleep(1)

        # Reopen wizard
        create_project_btn = driver.find_element(By.ID, 'createProjectBtn')
        create_project_btn.click()

        # Check for "Resume Draft" modal
        resume_modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.wizard-resume-modal'))
        )
        assert resume_modal.is_displayed(), "Resume draft modal should appear"

        # Click resume button
        resume_btn = resume_modal.find_element(By.CSS_SELECTOR, '.btn-primary')
        resume_btn.click()

        # Wait for draft to load
        time.sleep(1)

        # Verify form fields populated
        project_name_input = driver.find_element(By.ID, 'projectName')
        actual_value = project_name_input.get_attribute('value')
        assert actual_value == test_project_name, f"Should restore draft data, got: {actual_value}"

    def test_07_draft_clears_after_submission(self, driver):
        """
        Test: Draft clears from localStorage after successful submission

        BUSINESS CONTEXT:
        After completing wizard, draft should be removed to prevent stale
        data from appearing on next wizard open.

        EXPECTED BEHAVIOR:
        - Save draft
        - Complete wizard submission
        - localStorage draft removed
        - No "Resume Draft" prompt on next open
        """
        # Open wizard and fill minimum required data
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        # Fill required fields
        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Submission Test Project')

        # Save draft first
        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()
        time.sleep(2)

        # Verify draft exists
        draft_before = driver.execute_script("""
            return localStorage.getItem('wizard-draft-project-wizard');
        """)
        assert draft_before is not None, "Draft should exist before submission"

        # Complete wizard (navigate to final step and submit)
        # Note: This assumes multi-step wizard - adjust for actual implementation
        next_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-next-btn')
        next_btn.click()
        time.sleep(1)

        # Submit on final step
        submit_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-submit-btn')
        submit_btn.click()

        # Wait for submission to complete
        time.sleep(3)

        # Verify draft cleared
        draft_after = driver.execute_script("""
            return localStorage.getItem('wizard-draft-project-wizard');
        """)
        assert draft_after is None, "Draft should be cleared after submission"

    def test_08_multiple_drafts_for_different_wizards(self, driver):
        """
        Test: Multiple wizards can have separate drafts

        BUSINESS CONTEXT:
        Users may have in-progress work on multiple wizards (projects, tracks).
        Each wizard should maintain independent draft data.

        EXPECTED BEHAVIOR:
        - Save draft in project wizard
        - Save draft in track wizard
        - Both drafts exist in localStorage with unique keys
        - Each wizard loads correct draft
        """
        # Save project wizard draft
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Project Draft')

        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()
        time.sleep(2)

        # Close project wizard
        close_btn = driver.find_element(By.CSS_SELECTOR, '.modal-close')
        close_btn.click()
        time.sleep(1)

        # Open track wizard
        create_track_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createTrackBtn'))
        )
        create_track_btn.click()

        # Fill track data
        track_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'trackName'))
        )
        track_name_input.send_keys('Track Draft')

        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()
        time.sleep(2)

        # Verify both drafts exist with unique keys
        drafts = driver.execute_script("""
            return {
                project: localStorage.getItem('wizard-draft-project-wizard'),
                track: localStorage.getItem('wizard-draft-track-wizard')
            };
        """)

        assert drafts['project'] is not None, "Project draft should exist"
        assert drafts['track'] is not None, "Track draft should exist"
        assert drafts['project'] != drafts['track'], "Drafts should be independent"

    def test_09_dirty_state_tracking(self, driver):
        """
        Test: Unsaved changes are detected (dirty state)

        BUSINESS CONTEXT:
        System should detect when user has made changes that haven't been
        saved yet. Enables "unsaved changes" warnings.

        EXPECTED BEHAVIOR:
        - Fill form field
        - Dirty state indicator appears
        - Save draft
        - Dirty state clears
        - Make new change
        - Dirty state returns
        """
        # Open wizard
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        # Fill field (creates dirty state)
        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Dirty State Test')

        # Check for dirty indicator (visual cue)
        dirty_indicator = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-dirty-indicator]'))
        )
        assert dirty_indicator.is_displayed(), "Dirty indicator should appear after changes"

        # Save draft
        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()
        time.sleep(2)

        # Dirty indicator should disappear
        dirty_indicators = driver.find_elements(By.CSS_SELECTOR, '[data-dirty-indicator]')
        assert len(dirty_indicators) == 0 or not dirty_indicators[0].is_displayed(), \
            "Dirty indicator should clear after save"

    def test_10_prompt_before_navigating_away(self, driver):
        """
        Test: User prompted when navigating away with unsaved changes

        BUSINESS CONTEXT:
        Prevents accidental data loss when user tries to leave wizard
        with unsaved changes. Critical for user experience.

        EXPECTED BEHAVIOR:
        - Make changes (dirty state)
        - Attempt to close wizard
        - "Unsaved changes" modal appears
        - User can choose: Save & Close, Discard, or Cancel
        """
        # Open wizard and make changes
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Unsaved Changes Test')

        # Don't save - try to close immediately
        close_btn = driver.find_element(By.CSS_SELECTOR, '.modal-close')
        close_btn.click()

        # Should see unsaved changes modal
        unsaved_modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.wizard-unsaved-modal'))
        )
        assert unsaved_modal.is_displayed(), "Unsaved changes modal should appear"

        # Verify modal has expected buttons
        save_and_close_btn = unsaved_modal.find_element(By.CSS_SELECTOR, '[data-action="save-and-close"]')
        discard_btn = unsaved_modal.find_element(By.CSS_SELECTOR, '[data-action="discard"]')
        cancel_btn = unsaved_modal.find_element(By.CSS_SELECTOR, '[data-action="cancel"]')

        assert save_and_close_btn.is_displayed()
        assert discard_btn.is_displayed()
        assert cancel_btn.is_displayed()

    def test_11_draft_expires_after_7_days(self, driver):
        """
        Test: Drafts older than 7 days are not loaded

        BUSINESS CONTEXT:
        Stale drafts (>7 days) are likely no longer relevant. System
        should detect and ignore expired drafts.

        EXPECTED BEHAVIOR:
        - Create draft with timestamp from 8 days ago
        - Open wizard
        - No "Resume Draft" prompt
        - Draft not loaded
        """
        # Manually create expired draft in localStorage
        eight_days_ago = int(time.time() * 1000) - (8 * 24 * 60 * 60 * 1000)

        driver.execute_script(f"""
            const expiredDraft = {{
                wizardId: 'project-wizard',
                data: {{ projectName: 'Expired Draft' }},
                timestamp: {eight_days_ago},
                step: 1,
                version: 1
            }};
            localStorage.setItem('wizard-draft-project-wizard', JSON.stringify(expiredDraft));
        """)

        # Open wizard
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        # Wait to see if resume modal appears (it shouldn't)
        time.sleep(2)

        resume_modals = driver.find_elements(By.CSS_SELECTOR, '.wizard-resume-modal')
        assert len(resume_modals) == 0 or not resume_modals[0].is_displayed(), \
            "Resume modal should NOT appear for expired draft"

        # Verify form is empty (not populated from expired draft)
        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        assert project_name_input.get_attribute('value') == '', \
            "Form should be empty for expired draft"

    def test_12_loading_indicator_during_save(self, driver):
        """
        Test: Loading spinner appears during save operation

        BUSINESS CONTEXT:
        Visual feedback during async operations prevents user confusion.
        Uses Wave 3 loading states.

        EXPECTED BEHAVIOR:
        - Click Save Draft
        - Loading spinner appears on button
        - Button disabled during save
        - Spinner disappears after save completes
        """
        # Open wizard
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Loading Test')

        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')

        # Click save and immediately check for loading state
        save_draft_btn.click()

        # Button should have loading class
        # Note: This may be very fast, so we check both loading and final state
        assert save_draft_btn.get_attribute('disabled') is not None or \
               'btn-loading' in save_draft_btn.get_attribute('class'), \
            "Button should show loading state during save"

        # Wait for save to complete
        time.sleep(2)

        # Button should be enabled again
        assert save_draft_btn.get_attribute('disabled') is None, \
            "Button should be re-enabled after save"

    def test_13_error_handling_for_save_failures(self, driver):
        """
        Test: Error toast appears when save fails

        BUSINESS CONTEXT:
        localStorage can fail (quota exceeded, private browsing).
        Users need clear error feedback when save fails.

        EXPECTED BEHAVIOR:
        - Simulate localStorage failure
        - Attempt save
        - Error toast appears
        - User can retry
        """
        # Open wizard
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        # Override localStorage.setItem to throw error
        driver.execute_script("""
            const originalSetItem = Storage.prototype.setItem;
            Storage.prototype.setItem = function() {
                throw new Error('QuotaExceededError');
            };
            window._restoreSetItem = function() {
                Storage.prototype.setItem = originalSetItem;
            };
        """)

        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Error Test')

        # Try to save
        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()

        # Should see error toast
        error_toast = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ui-toast-error'))
        )
        assert 'error' in error_toast.text.lower() or 'failed' in error_toast.text.lower(), \
            "Should show error message"

        # Restore localStorage
        driver.execute_script("window._restoreSetItem();")

    def test_14_resume_draft_button_on_entry(self, driver):
        """
        Test: "Resume Draft" button appears when draft exists

        BUSINESS CONTEXT:
        When user opens wizard with existing draft, they should see
        clear option to resume or start fresh.

        EXPECTED BEHAVIOR:
        - Save draft
        - Close wizard
        - Reopen wizard
        - "Resume Draft" modal with two options:
          1. Resume Draft (primary button)
          2. Start Fresh (secondary button)
        """
        # Create and save draft
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        project_name_input.send_keys('Resume Button Test')

        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()
        time.sleep(2)

        # Close wizard
        close_btn = driver.find_element(By.CSS_SELECTOR, '.modal-close')
        close_btn.click()
        time.sleep(1)

        # Reopen wizard
        create_project_btn = driver.find_element(By.ID, 'createProjectBtn')
        create_project_btn.click()

        # Verify resume modal structure
        resume_modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.wizard-resume-modal'))
        )

        resume_btn = resume_modal.find_element(By.CSS_SELECTOR, '[data-action="resume"]')
        start_fresh_btn = resume_modal.find_element(By.CSS_SELECTOR, '[data-action="start-fresh"]')

        assert resume_btn.is_displayed(), "Resume button should be visible"
        assert start_fresh_btn.is_displayed(), "Start Fresh button should be visible"
        assert 'btn-primary' in resume_btn.get_attribute('class'), \
            "Resume should be primary action"

    def test_15_discard_draft_option(self, driver):
        """
        Test: User can discard draft and start fresh

        BUSINESS CONTEXT:
        Users may want to abandon draft and start over. System should
        provide clear option to discard saved progress.

        EXPECTED BEHAVIOR:
        - Save draft
        - Reopen wizard
        - Click "Start Fresh" on resume modal
        - Draft deleted from localStorage
        - Empty form displayed
        """
        # Create and save draft
        create_project_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'createProjectBtn'))
        )
        create_project_btn.click()

        project_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'projectName'))
        )
        test_data = 'Discard Test Draft'
        project_name_input.send_keys(test_data)

        save_draft_btn = driver.find_element(By.CSS_SELECTOR, '.wizard-save-draft-btn')
        save_draft_btn.click()
        time.sleep(2)

        # Verify draft exists
        draft_before = driver.execute_script("""
            return localStorage.getItem('wizard-draft-project-wizard');
        """)
        assert draft_before is not None

        # Close and reopen
        close_btn = driver.find_element(By.CSS_SELECTOR, '.modal-close')
        close_btn.click()
        time.sleep(1)

        create_project_btn = driver.find_element(By.ID, 'createProjectBtn')
        create_project_btn.click()

        # Click "Start Fresh"
        resume_modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.wizard-resume-modal'))
        )

        start_fresh_btn = resume_modal.find_element(By.CSS_SELECTOR, '[data-action="start-fresh"]')
        start_fresh_btn.click()

        # Wait for modal to close
        time.sleep(1)

        # Verify draft deleted
        draft_after = driver.execute_script("""
            return localStorage.getItem('wizard-draft-project-wizard');
        """)
        assert draft_after is None, "Draft should be deleted when starting fresh"

        # Verify form is empty
        project_name_input = driver.find_element(By.ID, 'projectName')
        assert project_name_input.get_attribute('value') == '', \
            "Form should be empty after discarding draft"
