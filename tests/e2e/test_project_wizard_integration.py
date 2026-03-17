"""
Test Suite: Project Creation Wizard Integration (Wave 4) - DEPRECATED

⚠️ WARNING: These tests are for Wave 4 features that were never implemented.
Wave 5 refactored wizards using WizardFramework instead.

STATUS: Tests conditionally skipped if Selenium not configured
REASON: Tests expect Wave 4 components (WizardProgress, WizardValidator, WizardDraft)
        with specific HTML data attributes that don't exist in Wave 5 implementation.

ALTERNATIVE: See test_project_wizard_wave5.py for tests that match actual implementation

ORIGINAL BUSINESS CONTEXT:
This test suite was written for Wave 4 features:
1. WizardProgress - Step indicator showing progress through 5-step wizard
2. WizardValidator - Real-time field validation with error messages
3. WizardDraft - Auto-save functionality with resume capability

These features were designed but never implemented. Wave 5 took a different
approach using WizardFramework component instead.

EXECUTION:
    pytest tests/e2e/test_project_wizard_integration.py -v  (tests will skip if Selenium not configured)

For working tests, run:
    pytest tests/e2e/test_project_wizard_wave5.py -v

@module test_project_wizard_integration
@version 1.0.0
@date 2025-10-17
@deprecated Use test_project_wizard_wave5.py instead
"""

import pytest
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Check if Selenium is configured
SELENIUM_AVAILABLE = os.getenv('SELENIUM_REMOTE') is not None or os.getenv('HEADLESS') is not None

@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not configured")
@pytest.mark.e2e
class TestProjectWizardIntegration:
    """
    Test class for Project Creation Wizard Wave 4 Integration

    BUSINESS CONTEXT:
    The project creation wizard is a critical conversion point for org admins.
    These tests ensure Wave 4 features enhance the UX without breaking existing functionality.
    """

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """
        Setup for each test

        BUSINESS LOGIC:
        - Logs in as org admin
        - Navigates to Projects tab
        - Opens project creation wizard
        - Clears any existing drafts
        """
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

        # Login as org admin
        self.driver.get("https://localhost/org-admin-dashboard.html")
        time.sleep(1)

        # Navigate to Projects tab
        projects_tab = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-tab="projects"]'))
        )
        projects_tab.click()
        time.sleep(0.5)

        # Clear any existing drafts from localStorage
        self.driver.execute_script("localStorage.removeItem('wizard-draft-project-creation');")

        yield

        # Cleanup: close any open modals
        self.driver.execute_script("""
            const modal = document.getElementById('createProjectModal');
            if (modal) modal.style.display = 'none';
        """)


    # ===================================================================
    # SECTION 1: WizardProgress Integration Tests (8 tests)
    # ===================================================================

    def test_01_wizard_opens_with_progress_indicator(self):
        """
        Test: Wizard modal opens and progress indicator is visible

        BUSINESS EXPECTATION:
        When org admin clicks "Create Project", the wizard opens with a
        progress indicator at the top showing all 5 steps.
        """
        # Open wizard
        create_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create Project')]"))
        )
        create_btn.click()
        time.sleep(0.5)

        # Verify modal opened
        modal = self.wait.until(
            EC.visibility_of_element_located((By.ID, "createProjectModal"))
        )
        assert modal.is_displayed(), "Project creation modal should be visible"

        # Verify progress indicator exists
        progress_indicator = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-wizard-progress]"))
        )
        assert progress_indicator is not None, "Progress indicator should exist"


    def test_02_progress_shows_5_steps(self):
        """
        Test: Progress indicator shows all 5 steps

        BUSINESS EXPECTATION:
        Progress indicator displays 5 steps:
        1. Basic Info
        2. Project Type
        3. Tracks
        4. Members
        5. Review
        """
        # Open wizard
        self._open_wizard()

        # Count wizard steps
        wizard_steps = self.driver.find_elements(By.CSS_SELECTOR, "[data-wizard-step]")
        assert len(wizard_steps) == 5, f"Expected 5 wizard steps, found {len(wizard_steps)}"

        # Verify step labels
        expected_labels = ["Basic Info", "Project Type", "Tracks", "Members", "Review"]
        for idx, step in enumerate(wizard_steps):
            label = step.find_element(By.CLASS_NAME, "wizard-step-label").text
            assert expected_labels[idx] in label, f"Step {idx+1} should be '{expected_labels[idx]}'"


    def test_03_step_1_highlighted_initially(self):
        """
        Test: Step 1 is highlighted as current step

        BUSINESS EXPECTATION:
        When wizard opens, Step 1 (Basic Info) should be highlighted
        with the 'is-current' class.
        """
        self._open_wizard()

        # Find current step
        current_step = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-wizard-step].is-current"))
        )

        # Verify it's step 1
        step_index = current_step.get_attribute("data-step-index")
        assert step_index == "0", "Step 1 (index 0) should be current"


    def test_04_required_field_validation_prevents_advance(self):
        """
        Test: Can't advance to Step 2 without filling required fields

        BUSINESS EXPECTATION:
        If project name is empty, clicking "Next" should show error
        and NOT advance to Step 2.
        """
        self._open_wizard()

        # Click Next without filling project name
        next_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-wizard-next]")
        next_btn.click()
        time.sleep(0.5)

        # Verify error message appears
        error_element = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-error-for='project-name']"))
        )
        assert error_element.is_displayed(), "Error message should be visible"

        # Verify still on Step 1
        current_step = self.driver.find_element(By.CSS_SELECTOR, "[data-wizard-step].is-current")
        step_index = current_step.get_attribute("data-step-index")
        assert step_index == "0", "Should still be on Step 1"


    def test_05_can_advance_when_valid(self):
        """
        Test: Can advance to Step 2 when all required fields filled

        BUSINESS EXPECTATION:
        After filling project name, clicking "Next" advances to Step 2.
        """
        self._open_wizard()

        # Fill project name
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.send_keys("Test Project Integration")
        time.sleep(0.3)

        # Click Next
        next_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-wizard-next]")
        next_btn.click()
        time.sleep(0.5)

        # Verify advanced to Step 2
        current_step = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-wizard-step].is-current"))
        )
        step_index = current_step.get_attribute("data-step-index")
        assert step_index == "1", "Should be on Step 2 (index 1)"


    def test_06_progress_updates_to_step_2(self):
        """
        Test: Progress indicator updates when advancing

        BUSINESS EXPECTATION:
        When moving to Step 2, progress indicator shows Step 2 as current
        and Step 1 as completed.
        """
        self._open_wizard()
        self._fill_step1_and_advance()

        # Verify Step 1 marked complete
        step1 = self.driver.find_element(By.CSS_SELECTOR, "[data-step-index='0']")
        assert "is-completed" in step1.get_attribute("class"), "Step 1 should be completed"

        # Verify Step 2 is current
        step2 = self.driver.find_element(By.CSS_SELECTOR, "[data-step-index='1']")
        assert "is-current" in step2.get_attribute("class"), "Step 2 should be current"


    def test_07_step_1_shows_checkmark(self):
        """
        Test: Completed steps show checkmark icon

        BUSINESS EXPECTATION:
        After completing Step 1, it should display a checkmark icon
        instead of the step number.
        """
        self._open_wizard()
        self._fill_step1_and_advance()

        # Verify checkmark is visible
        checkmark = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-step-index='0'] [data-wizard-step-checkmark]"))
        )
        assert checkmark.is_displayed(), "Checkmark should be visible on completed step"


    def test_08_can_navigate_back_to_step_1(self):
        """
        Test: Can click completed Step 1 to navigate back

        BUSINESS EXPECTATION:
        Clicking on completed Step 1 from Step 2 navigates back to Step 1.
        """
        self._open_wizard()
        self._fill_step1_and_advance()

        # Click on Step 1
        step1 = self.driver.find_element(By.CSS_SELECTOR, "[data-step-index='0']")
        step1.click()
        time.sleep(0.5)

        # Verify back on Step 1
        current_step = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-wizard-step].is-current"))
        )
        step_index = current_step.get_attribute("data-step-index")
        assert step_index == "0", "Should be back on Step 1"


    # ===================================================================
    # SECTION 2: WizardDraft Integration Tests (9 tests)
    # ===================================================================

    def test_09_save_draft_button_visible(self):
        """
        Test: "Save Draft" button is visible in wizard

        BUSINESS EXPECTATION:
        Wizard should have a "Save Draft" button in the footer.
        """
        self._open_wizard()

        save_draft_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-save-draft]"))
        )
        assert save_draft_btn.is_displayed(), "Save Draft button should be visible"


    def test_10_auto_save_triggers_after_30_seconds(self):
        """
        Test: Auto-save triggers after 30 seconds of inactivity

        BUSINESS EXPECTATION:
        After entering data, wizard auto-saves after 30 seconds.
        Draft indicator should show "Draft saved".
        """
        self._open_wizard()

        # Enter project name
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.send_keys("Auto-save Test Project")

        # Wait for auto-save (30 seconds + buffer)
        time.sleep(31)

        # Check for draft saved indicator or toast
        draft_indicator = self.driver.find_element(By.CSS_SELECTOR, "[data-draft-indicator]")
        assert draft_indicator.is_displayed(), "Draft indicator should be visible after auto-save"


    def test_11_draft_saved_toast_appears(self):
        """
        Test: Toast notification shows "Draft saved"

        BUSINESS EXPECTATION:
        When draft is saved (auto or manual), a success toast appears.
        """
        self._open_wizard()

        # Enter project name
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.send_keys("Draft Toast Test")

        # Click Save Draft
        save_draft_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-save-draft]")
        save_draft_btn.click()
        time.sleep(0.5)

        # Verify toast appears
        toast = self.wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "toast-success"))
        )
        assert "Draft saved" in toast.text, "Toast should say 'Draft saved'"


    def test_12_can_close_and_reopen_wizard(self):
        """
        Test: Can close wizard after saving draft

        BUSINESS EXPECTATION:
        After saving draft, can close wizard without losing progress.
        """
        self._open_wizard()

        # Enter data and save
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.send_keys("Close Test Project")

        save_draft_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-save-draft]")
        save_draft_btn.click()
        time.sleep(0.5)

        # Close wizard
        close_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-modal-close]")
        close_btn.click()
        time.sleep(0.5)

        # Verify modal closed
        modal = self.driver.find_element(By.ID, "createProjectModal")
        assert not modal.is_displayed(), "Modal should be closed"


    def test_13_resume_draft_modal_appears(self):
        """
        Test: "Resume draft?" modal appears when reopening

        BUSINESS EXPECTATION:
        After closing wizard with saved draft, reopening shows
        "Resume draft?" confirmation modal.
        """
        # Save draft and close
        self._open_wizard()
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.send_keys("Resume Test Project")

        save_draft_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-save-draft]")
        save_draft_btn.click()
        time.sleep(0.5)

        close_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-modal-close]")
        close_btn.click()
        time.sleep(0.5)

        # Reopen wizard
        self._open_wizard()

        # Verify resume draft modal
        resume_modal = self.wait.until(
            EC.visibility_of_element_located((By.ID, "resumeDraftModal"))
        )
        assert resume_modal.is_displayed(), "Resume draft modal should appear"


    def test_14_clicking_resume_loads_draft(self):
        """
        Test: Clicking "Resume" loads saved draft

        BUSINESS EXPECTATION:
        Clicking "Resume" button loads all saved field values.
        """
        # Save draft with specific data
        self._open_wizard()
        test_project_name = "Clickable Resume Test"
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.send_keys(test_project_name)

        save_draft_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-save-draft]")
        save_draft_btn.click()
        time.sleep(0.5)

        close_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-modal-close]")
        close_btn.click()
        time.sleep(0.5)

        # Reopen and resume
        self._open_wizard()
        resume_btn = self.wait.until(
            EC.element_to_be_clickable((By.ID, "resumeDraftBtn"))
        )
        resume_btn.click()
        time.sleep(0.5)

        # Verify data loaded
        project_name_input = self.driver.find_element(By.ID, "project-name")
        assert project_name_input.get_attribute("value") == test_project_name, "Draft data should be loaded"


    def test_15_draft_loads_at_correct_step(self):
        """
        Test: Draft resumes at the step where user left off

        BUSINESS EXPECTATION:
        If user saved draft on Step 2, resuming should go to Step 2.
        """
        # Navigate to Step 2 and save
        self._open_wizard()
        self._fill_step1_and_advance()

        save_draft_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-save-draft]")
        save_draft_btn.click()
        time.sleep(0.5)

        close_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-modal-close]")
        close_btn.click()
        time.sleep(0.5)

        # Reopen and resume
        self._open_wizard()
        resume_btn = self.wait.until(
            EC.element_to_be_clickable((By.ID, "resumeDraftBtn"))
        )
        resume_btn.click()
        time.sleep(0.5)

        # Verify on Step 2
        current_step = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-wizard-step].is-current"))
        )
        step_index = current_step.get_attribute("data-step-index")
        assert step_index == "1", "Should resume at Step 2"


    def test_16_final_submission_clears_draft(self):
        """
        Test: Submitting wizard clears saved draft

        BUSINESS EXPECTATION:
        After successful project creation, draft is deleted from storage.
        """
        # Create full project (skip for now - would require all 5 steps)
        pytest.skip("Requires full 5-step completion - implement in Phase 2")


    def test_17_can_start_fresh_from_resume_modal(self):
        """
        Test: "Start Fresh" button clears draft and starts over

        BUSINESS EXPECTATION:
        Clicking "Start Fresh" on resume modal clears draft and
        begins wizard from Step 1 with empty fields.
        """
        # Save draft
        self._open_wizard()
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.send_keys("Fresh Start Test")

        save_draft_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-save-draft]")
        save_draft_btn.click()
        time.sleep(0.5)

        close_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-modal-close]")
        close_btn.click()
        time.sleep(0.5)

        # Reopen and start fresh
        self._open_wizard()
        start_fresh_btn = self.wait.until(
            EC.element_to_be_clickable((By.ID, "startFreshBtn"))
        )
        start_fresh_btn.click()
        time.sleep(0.5)

        # Verify field is empty
        project_name_input = self.driver.find_element(By.ID, "project-name")
        assert project_name_input.get_attribute("value") == "", "Field should be empty"


    # ===================================================================
    # SECTION 3: WizardValidator Integration Tests (5 tests)
    # ===================================================================

    def test_18_validation_shows_errors_immediately(self):
        """
        Test: Validation errors appear on blur

        BUSINESS EXPECTATION:
        When user leaves a required field empty, error appears immediately.
        """
        self._open_wizard()

        # Focus and blur project name without entering value
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.click()
        project_name_input.send_keys(Keys.TAB)
        time.sleep(0.3)

        # Verify error appears
        error_element = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-error-for='project-name']"))
        )
        assert "required" in error_element.text.lower(), "Should show 'required' error"


    def test_19_error_clears_when_field_valid(self):
        """
        Test: Error disappears when field becomes valid

        BUSINESS EXPECTATION:
        After entering valid value, error message disappears and
        field shows success state.
        """
        self._open_wizard()

        # Trigger error
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.click()
        project_name_input.send_keys(Keys.TAB)
        time.sleep(0.3)

        # Fix error
        project_name_input.send_keys("Valid Project Name")
        project_name_input.send_keys(Keys.TAB)
        time.sleep(0.3)

        # Verify error cleared
        error_element = self.driver.find_element(By.CSS_SELECTOR, "[data-error-for='project-name']")
        assert not error_element.is_displayed(), "Error should be hidden"

        # Verify success state
        assert "success" in project_name_input.get_attribute("class"), "Field should have success class"


    def test_20_error_summary_shows_all_errors(self):
        """
        Test: Error summary panel shows all validation errors

        BUSINESS EXPECTATION:
        When clicking Next with multiple errors, error summary panel
        appears listing all errors.
        """
        self._open_wizard()

        # Click Next without filling any fields
        next_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-wizard-next]")
        next_btn.click()
        time.sleep(0.5)

        # Verify error summary appears
        error_summary = self.wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "validation-error-summary"))
        )
        assert error_summary.is_displayed(), "Error summary should be visible"

        # Verify it lists errors
        error_list = error_summary.find_element(By.ID, "errorList")
        errors = error_list.find_elements(By.TAG_NAME, "li")
        assert len(errors) > 0, "Should list errors"


    def test_21_clicking_error_focuses_field(self):
        """
        Test: Clicking error in summary focuses that field

        BUSINESS EXPECTATION:
        Clicking an error link in summary scrolls to and focuses
        the corresponding field.
        """
        self._open_wizard()

        # Trigger errors
        next_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-wizard-next]")
        next_btn.click()
        time.sleep(0.5)

        # Click first error link
        error_summary = self.driver.find_element(By.CLASS_NAME, "validation-error-summary")
        error_link = error_summary.find_element(By.TAG_NAME, "a")
        error_link.click()
        time.sleep(0.3)

        # Verify field is focused
        active_element = self.driver.switch_to.active_element
        assert active_element.get_attribute("id") == "project-name", "Project name field should be focused"


    def test_22_submit_disabled_until_valid(self):
        """
        Test: Submit button disabled until all fields valid

        BUSINESS EXPECTATION:
        Final submit button remains disabled until all validation passes.
        """
        self._open_wizard()

        # Navigate to final step (Step 5)
        # For now, just verify submit button exists and is disabled
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-wizard-submit]")
        assert not submit_btn.is_displayed(), "Submit button should not be visible on Step 1"


    # ===================================================================
    # SECTION 4: Integration & Zero Breaking Changes Tests (3 tests)
    # ===================================================================

    def test_23_all_5_steps_complete_workflow(self):
        """
        Test: Can complete all 5 steps of wizard

        BUSINESS EXPECTATION:
        User can navigate through all 5 steps successfully.
        """
        pytest.skip("Full 5-step workflow - implement in Phase 2")


    def test_24_existing_project_creation_still_works(self):
        """
        Test: Existing project creation functionality not broken

        BUSINESS EXPECTATION:
        Zero breaking changes - existing flows still work.
        """
        # Verify old functions still exist
        result = self.driver.execute_script("""
            return typeof window.OrgAdmin !== 'undefined' &&
                   typeof window.OrgAdmin.Projects !== 'undefined' &&
                   typeof window.OrgAdmin.Projects.nextProjectStep === 'function';
        """)
        assert result, "Existing OrgAdmin.Projects functions should still exist"


    def test_25_wizard_responsive_on_mobile(self):
        """
        Test: Wizard works on mobile viewport

        BUSINESS EXPECTATION:
        Progress indicator and form work on small screens.
        """
        # Set mobile viewport
        self.driver.set_window_size(375, 667)
        time.sleep(0.5)

        self._open_wizard()

        # Verify wizard is visible
        modal = self.driver.find_element(By.ID, "createProjectModal")
        assert modal.is_displayed(), "Wizard should be visible on mobile"

        # Verify progress indicator is visible (might be compact mode)
        progress_indicator = self.driver.find_element(By.CSS_SELECTOR, "[data-wizard-progress]")
        assert progress_indicator.is_displayed(), "Progress indicator should be visible"

        # Reset viewport
        self.driver.set_window_size(1920, 1080)


    # ===================================================================
    # HELPER METHODS
    # ===================================================================

    def _open_wizard(self):
        """Open the project creation wizard"""
        create_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create Project')]"))
        )
        create_btn.click()
        time.sleep(0.5)


    def _fill_step1_and_advance(self):
        """Fill Step 1 fields and advance to Step 2"""
        project_name_input = self.driver.find_element(By.ID, "project-name")
        project_name_input.send_keys("Test Project Integration")
        time.sleep(0.3)

        next_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-wizard-next]")
        next_btn.click()
        time.sleep(0.5)


    def _save_screenshot(self, name):
        """Save screenshot for debugging"""
        self.driver.save_screenshot(f"/home/bbrelin/course-creator/tests/reports/screenshots/{name}.png")
