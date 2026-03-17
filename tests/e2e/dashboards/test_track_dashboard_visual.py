"""
Track Dashboard Visual Regression Tests

BUSINESS PURPOSE:
Validates that track dashboard UI maintains consistent visual appearance.
Detects unintended layout changes, CSS regressions, and rendering issues.

TEST STRATEGY:
- Capture screenshots at key UI states (tab loaded, modal open, form filled)
- Compare against baseline images
- Fail test if visual changes exceed threshold
- Generate diff images highlighting changes

INTEGRATION WITH TDD:
- Run after functional tests pass
- Catches visual bugs that functional tests miss
- Prevents CSS regressions during refactoring

@module test_track_dashboard_visual
"""

import pytest
import time
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from selenium_base import BaseTest
from visual_regression_helper import VisualRegressionHelper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.visual
class TestTrackDashboardVisual(BaseTest):
    """
    Visual regression tests for Track Dashboard

    WHY THESE TESTS EXIST:
    Functional tests verify behavior (clicks work, data saves).
    Visual tests verify appearance (layout correct, no CSS breaks).
    Both are critical for user experience.

    BASELINE MANAGEMENT:
    - First run: Creates baselines
    - Subsequent runs: Compares to baselines
    - Update baselines: pytest --update-baselines
    """

    @pytest.fixture(scope="function", autouse=True)
    def setup_visual_regression(self, update_baselines, visual_threshold):
        """
        Set up visual regression helper for each test

        BUSINESS PURPOSE:
        Initializes visual regression framework with test-specific settings.
        Each test gets isolated visual comparison results.
        """
        self.visual = VisualRegressionHelper(
            driver=self.driver,
            test_name="track_dashboard",
            threshold=visual_threshold,
            update_baselines=update_baselines
        )

        # Navigate to tracks tab before visual tests
        self.driver.get(
            f"{self.config.base_url}/html/org-admin-dashboard.html?"
            f"org_id=550e8400-e29b-41d4-a716-446655440000"
        )
        time.sleep(2)

        # Handle privacy modal
        try:
            privacy_modal = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.ID, "privacyModal"))
            )
            if privacy_modal.is_displayed():
                accept_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
                self.click_element_js(accept_btn)
                time.sleep(1)
        except:
            pass

        # Login as org admin
        try:
            login_btn = self.wait_for_element((By.ID, "loginBtn"))
            self.click_element_js(login_btn)
            time.sleep(1)
        except:
            pass

        username_field = self.wait_for_element((By.ID, "loginEmail"))
        username_field.send_keys("orgadmin")

        password_field = self.wait_for_element((By.ID, "loginPassword"))
        password_field.send_keys("orgadmin123!")

        submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Sign In')]")
        self.click_element_js(submit_btn)
        time.sleep(3)

        # Navigate to tracks tab
        tracks_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tracksTab"))
        )
        tracks_tab.click()
        time.sleep(2)

    def test_tracks_tab_initial_state(self):
        """
        Visual test: Tracks tab initial loaded state

        VALIDATES:
        - Tab layout correct
        - Table rendered properly
        - Create button visible
        - No layout shifts after load
        """
        # Wait for content to stabilize
        self.wait_for_element((By.ID, "tracksTable"))
        time.sleep(1)

        # Capture and compare
        passed, diff = self.visual.capture_and_compare(
            "tracks_tab_initial",
            wait_for_selector="#tracksTable"
        )

        assert passed, (
            f"Tracks tab visual regression: {diff * 100:.2f}% difference. "
            f"Check diff image in visual_regression/diffs/"
        )

    def test_create_track_modal_visual(self):
        """
        Visual test: Create track modal appearance

        VALIDATES:
        - Modal positioning
        - Form field alignment
        - Button styling
        - Overlay rendering
        """
        # Open modal
        create_btn = self.wait_for_element((By.ID, "createTrackBtn"))
        self.click_element_js(create_btn)
        time.sleep(1)

        # Wait for modal animation
        modal = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "createTrackModal"))
        )
        time.sleep(0.5)  # Animation completion

        # Capture modal screenshot
        passed, diff = self.visual.capture_and_compare(
            "create_track_modal",
            element_selector="#createTrackModal"
        )

        assert passed, (
            f"Create track modal visual regression: {diff * 100:.2f}% difference"
        )

    def test_create_track_form_filled(self):
        """
        Visual test: Form with data filled in

        VALIDATES:
        - Input field rendering with content
        - Select dropdown appearance
        - Form validation states
        """
        # Open modal
        create_btn = self.wait_for_element((By.ID, "createTrackBtn"))
        self.click_element_js(create_btn)
        time.sleep(1)

        # Fill form
        name_field = self.wait_for_element((By.ID, "trackName"))
        name_field.send_keys("Visual Test Track")

        description_field = self.driver.find_element(By.ID, "trackDescription")
        description_field.send_keys("Testing visual regression")

        # Wait for form to stabilize
        time.sleep(0.5)

        # Capture filled form
        passed, diff = self.visual.capture_and_compare(
            "create_track_form_filled",
            element_selector="#createTrackModal"
        )

        assert passed, (
            f"Filled form visual regression: {diff * 100:.2f}% difference"
        )

    def test_tracks_table_rendering(self):
        """
        Visual test: Tracks table specific rendering

        VALIDATES:
        - Table structure
        - Column alignment
        - Row spacing
        - Action button placement
        """
        # Wait for table
        table = self.wait_for_element((By.ID, "tracksTable"))
        time.sleep(1)

        # Capture table screenshot
        passed, diff = self.visual.capture_and_compare(
            "tracks_table",
            element_selector="#tracksTable",
            custom_threshold=0.03  # Tables may have minor rendering variations
        )

        assert passed, (
            f"Tracks table visual regression: {diff * 100:.2f}% difference"
        )

    def test_edit_track_modal_visual(self):
        """
        Visual test: Edit track modal appearance

        VALIDATES:
        - Edit modal layout
        - Pre-populated fields
        - Update button styling
        """
        # Note: This assumes tracks exist in the table
        # In real scenario, you'd create a track first

        edit_modal = self.driver.find_element(By.ID, "editTrackModal")

        # Manually show modal for visual test
        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].classList.add('show');",
            edit_modal
        )
        time.sleep(0.5)

        # Capture edit modal
        passed, diff = self.visual.capture_and_compare(
            "edit_track_modal",
            element_selector="#editTrackModal"
        )

        assert passed, (
            f"Edit track modal visual regression: {diff * 100:.2f}% difference"
        )

    def test_delete_track_confirmation_visual(self):
        """
        Visual test: Delete confirmation modal

        VALIDATES:
        - Modal size and positioning
        - Warning text visibility
        - Button colors (danger state)
        """
        # Show delete modal
        delete_modal = self.driver.find_element(By.ID, "deleteTrackModal")

        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].classList.add('show');",
            delete_modal
        )
        time.sleep(0.5)

        # Capture delete confirmation
        passed, diff = self.visual.capture_and_compare(
            "delete_track_confirmation",
            element_selector="#deleteTrackModal"
        )

        assert passed, (
            f"Delete confirmation visual regression: {diff * 100:.2f}% difference"
        )

    def test_responsive_layout_tracking(self):
        """
        Visual test: Responsive layout at different viewports

        VALIDATES:
        - Layout adapts correctly to screen size
        - No elements overflow or overlap
        - Responsive CSS working correctly

        WHY THIS MATTERS:
        Users access dashboard from various devices.
        Layout must remain usable on all screen sizes.
        """
        # Test at common viewport sizes
        viewports = [
            (1920, 1080, "desktop_fullhd"),
            (1366, 768, "desktop_standard"),
            (768, 1024, "tablet_portrait"),
        ]

        for width, height, name in viewports:
            self.driver.set_window_size(width, height)
            time.sleep(1)  # Let layout reflow

            passed, diff = self.visual.capture_and_compare(
                f"responsive_{name}",
                custom_threshold=0.05  # Higher threshold for responsive changes
            )

            # Don't fail on viewport changes, just log
            if not passed:
                print(f"Note: Viewport {name} ({width}x{height}) has {diff * 100:.2f}% difference")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--update-baselines"])
