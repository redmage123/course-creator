"""
E2E Selenium Tests for Wizard Progress Indicator System

BUSINESS CONTEXT:
Tests the visual wizard progress indicator component that shows users:
- Current step position
- Completed steps
- Remaining steps
- Visual progress line
- Step navigation capabilities

This component is critical for user experience in multi-step flows:
- Project creation wizard (5 steps)
- Track creation wizard (4 steps)
- Course creation wizard (6 steps)
- Organization registration wizard (3 steps)

TECHNICAL IMPLEMENTATION:
- Tests WizardProgress JavaScript class
- Verifies CSS styling with OUR blue color (#2563eb)
- Validates accessibility (ARIA, keyboard navigation)
- Tests responsive behavior (mobile/desktop)
- Uses 8px spacing system
- Validates 200ms transitions

TDD METHODOLOGY:
RED PHASE - These tests will fail until implementation is complete
Tests drive the implementation of wizard-progress.css and wizard-progress.js

DESIGN REQUIREMENTS:
- Uses OUR blue color scheme (#2563eb)
- No external references or design system toggles
- Direct style application
- 8px spacing system throughout
- 200ms smooth transitions
"""

import pytest
import time
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

sys.path.insert(0, '/home/bbrelin/course-creator/tests/e2e')
from selenium_base import BaseTest


class TestWizardProgressIndicator(BaseTest):
    """
    E2E tests for wizard progress indicator visual component
    """

    def setup_method(self, method):
        """Set up before each test"""
        super().setup_method(method)
        # Create a test page with wizard progress indicator
        self.create_test_wizard_page()

    def create_test_wizard_page(self):
        """
        Create a test HTML page with wizard progress indicator

        BUSINESS LOGIC:
        Sets up a minimal test environment to test the wizard progress component
        """
        test_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wizard Progress Test</title>
    <link rel="stylesheet" href="/css/base/variables.css">
    <link rel="stylesheet" href="/css/modern-ui/design-system.css">
    <link rel="stylesheet" href="/css/modern-ui/wizard-progress.css">
</head>
<body>
    <div class="test-container" style="padding: 40px; max-width: 800px; margin: 0 auto;">
        <h1>Wizard Progress Indicator Test</h1>

        <!-- Wizard Progress Container -->
        <div id="wizard-progress-container"></div>

        <!-- Test Controls -->
        <div style="margin-top: 40px;">
            <button id="next-btn" class="btn btn-primary">Next Step</button>
            <button id="prev-btn" class="btn btn-secondary">Previous Step</button>
            <button id="complete-btn" class="btn btn-success">Mark Complete</button>
        </div>
    </div>

    <script type="module">
        import { WizardProgress } from '/js/modules/wizard-progress.js';

        // Initialize wizard with 5 steps
        const wizard = new WizardProgress({
            container: '#wizard-progress-container',
            steps: [
                { id: 'basic-info', label: 'Basic Info', description: 'Project details' },
                { id: 'configuration', label: 'Configuration', description: 'Settings' },
                { id: 'tracks', label: 'Tracks', description: 'Learning paths' },
                { id: 'review', label: 'Review', description: 'Confirm details' },
                { id: 'complete', label: 'Complete', description: 'Finish setup' }
            ],
            currentStep: 0,
            allowBackNavigation: true
        });

        // Wire up test controls
        document.getElementById('next-btn').addEventListener('click', () => {
            wizard.nextStep();
        });

        document.getElementById('prev-btn').addEventListener('click', () => {
            wizard.previousStep();
        });

        document.getElementById('complete-btn').addEventListener('click', () => {
            wizard.markComplete(wizard.getCurrentStep());
        });

        // Make wizard globally accessible for testing
        window.testWizard = wizard;
    </script>
</body>
</html>
        """

        # Navigate to base URL and inject test HTML
        self.driver.get(f"{self.base_url}/")
        self.driver.execute_script(f"""
            document.open();
            document.write({repr(test_html)});
            document.close();
        """)

        time.sleep(1)  # Allow page to load

    def test_01_wizard_progress_displays_all_steps(self):
        """
        TEST: Wizard progress indicator displays all steps
        REQUIREMENT: Shows all 5 steps with labels
        SUCCESS CRITERIA: 5 step elements are rendered
        """
        # Wait for wizard to render
        try:
            wizard_container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "wizard-progress"))
            )
        except TimeoutException:
            pytest.fail("Wizard progress container did not render")

        # Find all step elements
        steps = self.driver.find_elements(By.CSS_SELECTOR, ".wizard-step")

        assert len(steps) == 5, f"Expected 5 steps, found {len(steps)}"

        # Verify step labels
        expected_labels = ["Basic Info", "Configuration", "Tracks", "Review", "Complete"]
        for i, step in enumerate(steps):
            label = step.find_element(By.CLASS_NAME, "wizard-step-label")
            assert expected_labels[i] in label.text, f"Step {i+1} should have label '{expected_labels[i]}'"

        self.take_screenshot("wizard_displays_all_steps")

    def test_02_current_step_highlighted_with_our_blue(self):
        """
        TEST: Current step is highlighted with OUR blue color (#2563eb)
        REQUIREMENT: Visual distinction for current step using #2563eb
        SUCCESS CRITERIA: Current step has blue border/background
        """
        # Find current step (step 1)
        current_step = self.driver.find_element(By.CSS_SELECTOR, ".wizard-step.is-current")

        # Check computed style for OUR blue color
        border_color = current_step.value_of_css_property("border-color")
        background_color = current_step.value_of_css_property("background-color")

        # Convert #2563eb to rgb(37, 99, 235)
        expected_rgb = "rgb(37, 99, 235)"

        # Either border or background should use OUR blue
        has_our_blue = expected_rgb in border_color or expected_rgb in background_color

        assert has_our_blue, f"Current step should use OUR blue (#2563eb), found border: {border_color}, bg: {background_color}"

        self.take_screenshot("current_step_highlighted_blue")

    def test_03_completed_steps_show_checkmark_icon(self):
        """
        TEST: Completed steps display checkmark icon
        REQUIREMENT: Visual feedback for completed steps
        SUCCESS CRITERIA: Checkmark icon visible on completed steps
        """
        # Mark step 0 as complete and advance
        self.driver.execute_script("window.testWizard.nextStep();")
        time.sleep(0.3)  # Wait for transition

        # Find step 1 (now completed)
        completed_step = self.driver.find_element(By.CSS_SELECTOR, ".wizard-step.is-completed")

        # Check for checkmark icon
        checkmark = completed_step.find_element(By.CLASS_NAME, "wizard-step-icon")

        assert checkmark.is_displayed(), "Checkmark icon should be visible on completed step"

        # Verify SVG exists
        svg = checkmark.find_element(By.TAG_NAME, "svg")
        assert svg is not None, "Checkmark should be an SVG icon"

        self.take_screenshot("completed_step_shows_checkmark")

    def test_04_future_steps_show_step_number(self):
        """
        TEST: Future steps display step number (not checkmark)
        REQUIREMENT: Clear indication of upcoming steps
        SUCCESS CRITERIA: Step numbers visible for pending steps
        """
        # Future steps should show numbers
        future_steps = self.driver.find_elements(By.CSS_SELECTOR, ".wizard-step.is-pending")

        assert len(future_steps) >= 1, "Should have at least one pending step"

        # Check that step numbers are visible
        for step in future_steps:
            step_number = step.find_element(By.CLASS_NAME, "wizard-step-number")
            assert step_number.is_displayed(), "Step number should be visible for pending steps"

        self.take_screenshot("future_steps_show_numbers")

    def test_05_completed_steps_are_clickable(self):
        """
        TEST: Completed steps are clickable for back navigation
        REQUIREMENT: Users can navigate back to completed steps
        SUCCESS CRITERIA: Clicking completed step navigates to that step
        """
        # Advance to step 2
        self.driver.execute_script("window.testWizard.nextStep();")
        time.sleep(0.3)
        self.driver.execute_script("window.testWizard.nextStep();")
        time.sleep(0.3)

        # Current step should be 1 (zero-indexed)
        current = self.driver.execute_script("return window.testWizard.getCurrentStep();")
        assert current == 1, "Should be on step 2 (index 1)"

        # Click on step 1 (completed)
        completed_step = self.driver.find_element(By.CSS_SELECTOR, ".wizard-step.is-completed")
        completed_step.click()

        time.sleep(0.3)  # Wait for transition

        # Should now be on step 0
        current = self.driver.execute_script("return window.testWizard.getCurrentStep();")
        assert current == 0, "Should have navigated back to step 1 (index 0)"

        self.take_screenshot("completed_step_clickable_navigation")

    def test_06_future_steps_not_clickable(self):
        """
        TEST: Future steps are NOT clickable
        REQUIREMENT: Prevent skipping ahead to incomplete steps
        SUCCESS CRITERIA: Clicking future step does not navigate
        """
        # Try to click a future step
        current = self.driver.execute_script("return window.testWizard.getCurrentStep();")

        future_step = self.driver.find_element(By.CSS_SELECTOR, ".wizard-step.is-pending")
        future_step.click()

        time.sleep(0.3)

        # Should still be on same step
        current_after = self.driver.execute_script("return window.testWizard.getCurrentStep();")
        assert current == current_after, "Should not navigate to future steps"

        self.take_screenshot("future_step_not_clickable")

    def test_07_progress_line_connects_steps(self):
        """
        TEST: Progress line visually connects steps
        REQUIREMENT: Visual connection between steps
        SUCCESS CRITERIA: Progress line element exists and spans steps
        """
        # Find progress line
        progress_line = self.driver.find_element(By.CLASS_NAME, "wizard-progress-line")

        assert progress_line.is_displayed(), "Progress line should be visible"

        # Check width spans across steps
        line_width = progress_line.size['width']
        assert line_width > 0, "Progress line should have width"

        self.take_screenshot("progress_line_connects_steps")

    def test_08_progress_line_fills_with_our_blue(self):
        """
        TEST: Progress line fills with OUR blue (#2563eb) for completed sections
        REQUIREMENT: Visual progress indication
        SUCCESS CRITERIA: Filled portion uses #2563eb
        """
        # Advance to step 2 (marking step 1 complete)
        self.driver.execute_script("window.testWizard.nextStep();")
        time.sleep(0.3)

        # Find progress line fill
        progress_fill = self.driver.find_element(By.CLASS_NAME, "wizard-progress-line-fill")

        # Check background color
        bg_color = progress_fill.value_of_css_property("background-color")

        # Should be OUR blue: rgb(37, 99, 235)
        expected_rgb = "rgb(37, 99, 235)"

        assert expected_rgb in bg_color, f"Progress fill should use OUR blue (#2563eb), found: {bg_color}"

        # Check width increases as we progress
        fill_width = progress_fill.value_of_css_property("width")
        assert fill_width != "0px", "Progress fill should have width > 0 after advancing"

        self.take_screenshot("progress_line_fills_blue")

    def test_09_step_transitions_smooth_200ms(self):
        """
        TEST: Step state transitions are smooth with 200ms duration
        REQUIREMENT: Polished animations
        SUCCESS CRITERIA: transition-duration is 200ms
        """
        # Check current step transition property
        current_step = self.driver.find_element(By.CSS_SELECTOR, ".wizard-step.is-current")

        transition = current_step.value_of_css_property("transition-duration")

        # Should be 0.2s (200ms)
        assert "0.2s" in transition or "200ms" in transition, f"Transition should be 200ms, found: {transition}"

        self.take_screenshot("step_transition_timing")

    def test_10_uses_8px_spacing_system(self):
        """
        TEST: Component uses 8px spacing system
        REQUIREMENT: Consistent spacing across platform
        SUCCESS CRITERIA: Padding/margins are multiples of 8px
        """
        # Check container padding
        container = self.driver.find_element(By.CLASS_NAME, "wizard-progress")

        padding = container.value_of_css_property("padding")
        # Parse padding value (e.g., "24px" -> 24)
        padding_values = [int(p.replace('px', '')) for p in padding.split() if 'px' in p]

        # All padding values should be multiples of 8
        for val in padding_values:
            assert val % 8 == 0, f"Padding {val}px should be multiple of 8px"

        self.take_screenshot("spacing_system_8px")

    def test_11_responsive_mobile_vertical_layout(self):
        """
        TEST: Mobile layout switches to vertical orientation
        REQUIREMENT: Responsive design for mobile devices
        SUCCESS CRITERIA: Steps stack vertically on screens < 768px
        """
        # Resize to mobile width
        self.driver.set_window_size(375, 667)  # iPhone size
        time.sleep(0.5)  # Allow layout to adjust

        # Check if steps are stacked vertically
        steps = self.driver.find_elements(By.CSS_SELECTOR, ".wizard-step")

        if len(steps) >= 2:
            step1_y = steps[0].locations['y']
            step2_y = steps[1].locations['y']

            # On mobile, step 2 should be below step 1
            assert step2_y > step1_y, "Steps should stack vertically on mobile"

        self.take_screenshot("mobile_vertical_layout")

        # Reset to desktop size
        self.driver.set_window_size(1280, 720)

    def test_12_keyboard_navigation_support(self):
        """
        TEST: Keyboard navigation works for completed steps
        REQUIREMENT: Accessibility via keyboard
        SUCCESS CRITERIA: Enter/Space keys trigger navigation
        """
        # Advance to step 2
        self.driver.execute_script("window.testWizard.nextStep();")
        time.sleep(0.3)

        # Focus on completed step
        completed_step = self.driver.find_element(By.CSS_SELECTOR, ".wizard-step.is-completed")
        completed_step.click()  # Focus element

        # Press Enter key
        completed_step.send_keys(Keys.ENTER)
        time.sleep(0.3)

        # Should navigate back
        current = self.driver.execute_script("return window.testWizard.getCurrentStep();")
        assert current == 0, "Enter key should trigger navigation"

        self.take_screenshot("keyboard_navigation")

    def test_13_aria_labels_for_accessibility(self):
        """
        TEST: ARIA labels present for screen readers
        REQUIREMENT: Screen reader accessibility
        SUCCESS CRITERIA: All steps have aria-label attributes
        """
        steps = self.driver.find_elements(By.CSS_SELECTOR, ".wizard-step")

        for i, step in enumerate(steps):
            aria_label = step.get_attribute("aria-label")
            assert aria_label is not None, f"Step {i+1} should have aria-label"
            assert f"Step {i+1}" in aria_label, f"aria-label should include step number"

        # Check current step has aria-current
        current_step = self.driver.find_element(By.CSS_SELECTOR, ".wizard-step.is-current")
        aria_current = current_step.get_attribute("aria-current")
        assert aria_current == "step", "Current step should have aria-current='step'"

        self.take_screenshot("aria_labels_present")

    def test_14_step_count_displayed(self):
        """
        TEST: Step count indicator displays "Step X of Y"
        REQUIREMENT: Clear progress information
        SUCCESS CRITERIA: Text shows current position like "Step 1 of 5"
        """
        # Find step count element
        step_count = self.driver.find_element(By.CLASS_NAME, "wizard-step-count")

        count_text = step_count.text
        assert "Step 1 of 5" in count_text, f"Should show 'Step 1 of 5', found: {count_text}"

        # Advance and verify update
        self.driver.execute_script("window.testWizard.nextStep();")
        time.sleep(0.3)

        count_text = step_count.text
        assert "Step 2 of 5" in count_text, f"Should update to 'Step 2 of 5', found: {count_text}"

        self.take_screenshot("step_count_displayed")

    def test_15_completed_steps_have_checkmark_and_clickable_cursor(self):
        """
        TEST: Completed steps show pointer cursor indicating clickability
        REQUIREMENT: Visual affordance for interaction
        SUCCESS CRITERIA: cursor: pointer on completed steps
        """
        # Advance to create completed step
        self.driver.execute_script("window.testWizard.nextStep();")
        time.sleep(0.3)

        # Check cursor on completed step
        completed_step = self.driver.find_element(By.CSS_SELECTOR, ".wizard-step.is-completed")
        cursor = completed_step.value_of_css_property("cursor")

        assert cursor == "pointer", f"Completed steps should have cursor: pointer, found: {cursor}"

        self.take_screenshot("completed_step_pointer_cursor")

    def test_16_progress_percentage_calculation(self):
        """
        TEST: Progress percentage calculated correctly
        REQUIREMENT: Accurate progress tracking
        SUCCESS CRITERIA: getProgress() returns correct percentage
        """
        # Initial: Step 1 of 5 = 0%
        progress = self.driver.execute_script("return window.testWizard.getProgress();")
        assert progress == 0, f"Initial progress should be 0%, found: {progress}%"

        # After step 1: 20%
        self.driver.execute_script("window.testWizard.nextStep();")
        progress = self.driver.execute_script("return window.testWizard.getProgress();")
        assert progress == 20, f"Progress after 1 step should be 20%, found: {progress}%"

        # After step 2: 40%
        self.driver.execute_script("window.testWizard.nextStep();")
        progress = self.driver.execute_script("return window.testWizard.getProgress();")
        assert progress == 40, f"Progress after 2 steps should be 40%, found: {progress}%"

        self.take_screenshot("progress_percentage_calculation")

    def test_17_no_external_references_in_code(self):
        """
        TEST: Code contains no external references
        REQUIREMENT: Use OUR colors and design tokens only
        SUCCESS CRITERIA: No external library references in comments or code
        """
        # Read the CSS file
        css_content = self.driver.execute_script("""
            return fetch('/css/modern-ui/wizard-progress.css')
                .then(r => r.text())
                .catch(() => '');
        """)

        time.sleep(0.5)

        # Check for forbidden references (case-insensitive)
        forbidden = ['tailwind', 'bootstrap', 'material', 'ant-design', 'external']
        css_lower = css_content.lower() if isinstance(css_content, str) else ""

        for term in forbidden:
            assert term not in css_lower, f"CSS should not reference '{term}'"

        self.take_screenshot("no_external_references")

    def test_18_step_circle_size_32px(self):
        """
        TEST: Step circles are 32px (4 * 8px)
        REQUIREMENT: Consistent sizing with 8px system
        SUCCESS CRITERIA: Circle width and height are 32px
        """
        step_circle = self.driver.find_element(By.CLASS_NAME, "wizard-step-circle")

        width = step_circle.size['width']
        height = step_circle.size['height']

        # Should be approximately 32px (allow 1px tolerance for rounding)
        assert 31 <= width <= 33, f"Circle width should be 32px, found: {width}px"
        assert 31 <= height <= 33, f"Circle height should be 32px, found: {height}px"

        self.take_screenshot("step_circle_32px")

    def test_19_progress_line_width_calculation(self):
        """
        TEST: Progress line width increases correctly with completion
        REQUIREMENT: Visual progress feedback
        SUCCESS CRITERIA: Line width = (completed / total) * 100%
        """
        # Get initial width (should be 0)
        initial_width = self.driver.execute_script("""
            const fill = document.querySelector('.wizard-progress-line-fill');
            return parseFloat(fill.style.width);
        """)

        assert initial_width == 0, "Initial progress line width should be 0%"

        # Complete step 1 and advance
        self.driver.execute_script("window.testWizard.nextStep();")
        time.sleep(0.3)

        # Width should be 20% (1 of 5 steps)
        width = self.driver.execute_script("""
            const fill = document.querySelector('.wizard-progress-line-fill');
            return parseFloat(fill.style.width);
        """)

        assert width == 20, f"Progress line should be 20% after 1 step, found: {width}%"

        self.take_screenshot("progress_line_width_calculation")

    def test_20_wizard_complete_check(self):
        """
        TEST: isComplete() returns true when all steps completed
        REQUIREMENT: Completion detection
        SUCCESS CRITERIA: isComplete() is true after all steps done
        """
        # Initially incomplete
        is_complete = self.driver.execute_script("return window.testWizard.isComplete();")
        assert is_complete is False, "Wizard should not be complete initially"

        # Complete all steps
        for _ in range(5):
            self.driver.execute_script("window.testWizard.nextStep();")
            time.sleep(0.2)

        # Should now be complete
        is_complete = self.driver.execute_script("return window.testWizard.isComplete();")
        assert is_complete is True, "Wizard should be complete after all steps"

        self.take_screenshot("wizard_complete")


class TestWizardProgressIntegration(BaseTest):
    """
    Integration tests with actual project wizard
    """

    def test_21_integration_with_project_wizard(self):
        """
        TEST: Wizard progress integrates with project creation wizard
        REQUIREMENT: Real-world usage scenario
        SUCCESS CRITERIA: Progress indicator appears in project wizard
        """
        # This would test integration with actual org-admin dashboard
        # For now, we'll skip since it requires full app context
        pytest.skip("Integration test - requires full application context")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
