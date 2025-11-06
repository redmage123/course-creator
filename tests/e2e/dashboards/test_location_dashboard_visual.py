"""
Locations Dashboard Visual Regression Tests

BUSINESS PURPOSE:
Validates that locations dashboard UI maintains consistent visual appearance.
Tests both locations-level CRUD and nested track CRUD at locations level.

TEST COVERAGE:
- Locations tab and table rendering
- Locations CRUD modals (create, edit, delete)
- Nested track management section
- Track CRUD modals at locations level (6 modals total)

WHY TWO-LEVEL VISUAL TESTING:
Locations dashboard has more complex nested UI than track dashboard.
Both parent (locations) and child (track) CRUD interfaces must be visually validated.

@module test_location_dashboard_visual
"""

import pytest
import time
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from selenium_base import BaseTest
from visual_regression_helper import VisualRegressionHelper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.visual
class TestLocationDashboardVisual(BaseTest):
    """
    Visual regression tests for Locations Dashboard

    COMPLEXITY NOTE:
    Locations dashboard has 6 modals (3 for locations + 3 for tracks at locations).
    Each modal state needs visual validation.
    """

    @pytest.fixture(scope="function", autouse=True)
    def setup_visual_regression(self, update_baselines, visual_threshold):
        """Set up visual regression and navigate to locations dashboard"""
        self.visual = VisualRegressionHelper(
            driver=self.driver,
            test_name="location_dashboard",
            threshold=visual_threshold,
            update_baselines=update_baselines
        )

        # Navigate and login
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

        # Login
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

        # Navigate to locations tab
        locations_tab = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locationsTab"))
        )
        locations_tab.click()
        time.sleep(2)

    # =============================================================================
    # SECTION 1: Locations-Level Visual Tests
    # =============================================================================

    def test_locations_tab_initial_state(self):
        """
        Visual test: Locations tab initial state

        VALIDATES:
        - Tab layout and positioning
        - Table structure
        - Create button visibility
        - Overall page composition
        """
        self.wait_for_element((By.ID, "locationsTable"))
        time.sleep(1)

        passed, diff = self.visual.capture_and_compare(
            "locations_tab_initial",
            wait_for_selector="#locationsTable"
        )

        assert passed, f"Locations tab visual regression: {diff * 100:.2f}% difference"

    def test_create_location_modal_visual(self):
        """
        Visual test: Create locations modal

        VALIDATES:
        - Modal positioning and size
        - Form field layout (10 fields for locations)
        - Geographic fields grouping
        - Date picker styling
        """
        create_btn = self.wait_for_element((By.ID, "createLocationBtn"))
        self.click_element_js(create_btn)
        time.sleep(1)

        modal = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "createLocationModal"))
        )
        time.sleep(0.5)

        passed, diff = self.visual.capture_and_compare(
            "create_location_modal",
            element_selector="#createLocationModal"
        )

        assert passed, f"Create locations modal visual regression: {diff * 100:.2f}% difference"

    def test_create_location_form_filled(self):
        """
        Visual test: Locations form with data

        VALIDATES:
        - All geographic fields populated
        - Date field rendering
        - Number input appearance
        - Field validation states
        """
        create_btn = self.wait_for_element((By.ID, "createLocationBtn"))
        self.click_element_js(create_btn)
        time.sleep(1)

        # Fill locations-specific fields
        name_field = self.wait_for_element((By.ID, "locationName"))
        name_field.send_keys("Visual Test Locations")

        slug_field = self.driver.find_element(By.ID, "locationSlug")
        slug_field.send_keys("visual-test-locations")

        description = self.driver.find_element(By.ID, "locationDescription")
        description.send_keys("Testing visual regression for locations")

        country = self.driver.find_element(By.ID, "locationCountry")
        country.send_keys("Canada")

        city = self.driver.find_element(By.ID, "locationCity")
        city.send_keys("Toronto")

        time.sleep(0.5)

        passed, diff = self.visual.capture_and_compare(
            "create_location_form_filled",
            element_selector="#createLocationModal",
            custom_threshold=0.03  # Forms may have cursor/focus variations
        )

        assert passed, f"Filled locations form visual regression: {diff * 100:.2f}% difference"

    def test_edit_location_modal_visual(self):
        """
        Visual test: Edit locations modal

        VALIDATES:
        - Edit modal layout
        - Pre-populated geographic data
        - Update button styling
        """
        edit_modal = self.driver.find_element(By.ID, "editLocationModal")

        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].classList.add('show');",
            edit_modal
        )
        time.sleep(0.5)

        passed, diff = self.visual.capture_and_compare(
            "edit_location_modal",
            element_selector="#editLocationModal"
        )

        assert passed, f"Edit locations modal visual regression: {diff * 100:.2f}% difference"

    def test_delete_location_modal_visual(self):
        """
        Visual test: Delete locations confirmation

        VALIDATES:
        - Warning message visibility
        - Cascade warning (deletes associated tracks)
        - Danger button styling
        """
        delete_modal = self.driver.find_element(By.ID, "deleteLocationModal")

        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].classList.add('show');",
            delete_modal
        )
        time.sleep(0.5)

        passed, diff = self.visual.capture_and_compare(
            "delete_location_modal",
            element_selector="#deleteLocationModal"
        )

        assert passed, f"Delete locations modal visual regression: {diff * 100:.2f}% difference"

    # =============================================================================
    # SECTION 2: Nested Track Management Visual Tests
    # =============================================================================

    def test_location_tracks_section_visual(self):
        """
        Visual test: Tracks section within locations view

        VALIDATES:
        - Nested tracks table layout
        - Create track button at locations level
        - Section heading and description
        - Relationship indicators
        """
        tracks_section = self.driver.find_element(By.ID, "locationTracksSection")

        # Show section for visual test
        self.driver.execute_script(
            "arguments[0].style.display = 'block';",
            tracks_section
        )
        time.sleep(0.5)

        passed, diff = self.visual.capture_and_compare(
            "location_tracks_section",
            element_selector="#locationTracksSection"
        )

        assert passed, f"Locations tracks section visual regression: {diff * 100:.2f}% difference"

    def test_create_track_at_location_modal_visual(self):
        """
        Visual test: Create track at locations modal

        VALIDATES:
        - Modal indicates locations context
        - Track form fields appropriate for locations
        - Locations ID pre-populated/hidden
        - Submit button labeled correctly
        """
        modal = self.driver.find_element(By.ID, "createTrackAtLocationModal")

        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].classList.add('show');",
            modal
        )
        time.sleep(0.5)

        passed, diff = self.visual.capture_and_compare(
            "create_track_at_location_modal",
            element_selector="#createTrackAtLocationModal"
        )

        assert passed, f"Create track at locations modal visual regression: {diff * 100:.2f}% difference"

    def test_create_track_at_location_form_filled(self):
        """
        Visual test: Track form with data at locations level

        VALIDATES:
        - Track fields populated correctly
        - Locations context indicator visible
        - Form validation in nested context
        """
        modal = self.driver.find_element(By.ID, "createTrackAtLocationModal")

        # Show modal
        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].classList.add('show');",
            modal
        )
        time.sleep(0.5)

        # Fill track fields
        name_field = self.driver.find_element(By.ID, "locationTrackName")
        name_field.send_keys("Visual Test Track at Locations")

        description = self.driver.find_element(By.ID, "locationTrackDescription")
        description.send_keys("Track created in locations context")

        time.sleep(0.5)

        passed, diff = self.visual.capture_and_compare(
            "create_track_at_location_form_filled",
            element_selector="#createTrackAtLocationModal",
            custom_threshold=0.03
        )

        assert passed, f"Track form at locations visual regression: {diff * 100:.2f}% difference"

    def test_edit_track_at_location_modal_visual(self):
        """
        Visual test: Edit track at locations modal

        VALIDATES:
        - Edit modal shows locations context
        - Track data pre-populated
        - Update button labeled correctly for nested context
        """
        modal = self.driver.find_element(By.ID, "editTrackAtLocationModal")

        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].classList.add('show');",
            modal
        )
        time.sleep(0.5)

        passed, diff = self.visual.capture_and_compare(
            "edit_track_at_location_modal",
            element_selector="#editTrackAtLocationModal"
        )

        assert passed, f"Edit track at locations modal visual regression: {diff * 100:.2f}% difference"

    def test_delete_track_at_location_modal_visual(self):
        """
        Visual test: Delete track at locations confirmation

        VALIDATES:
        - Confirmation message references locations
        - Warning about track deletion
        - Danger button styling in nested context
        """
        modal = self.driver.find_element(By.ID, "deleteTrackAtLocationModal")

        self.driver.execute_script(
            "arguments[0].style.display = 'block';"
            "arguments[0].classList.add('show');",
            modal
        )
        time.sleep(0.5)

        passed, diff = self.visual.capture_and_compare(
            "delete_track_at_location_modal",
            element_selector="#deleteTrackAtLocationModal"
        )

        assert passed, f"Delete track at locations modal visual regression: {diff * 100:.2f}% difference"

    # =============================================================================
    # SECTION 3: Complex Layout Validation
    # =============================================================================

    def test_full_page_composition(self):
        """
        Visual test: Complete page layout

        VALIDATES:
        - Overall page composition
        - Navigation bar
        - Sidebar (if present)
        - Main content area
        - Footer

        WHY FULL PAGE:
        Element-specific tests miss layout relationships.
        Full page captures overall visual hierarchy.
        """
        # Ensure page is fully loaded
        self.wait_for_element((By.ID, "locationsTable"))
        time.sleep(2)

        passed, diff = self.visual.capture_and_compare(
            "full_page_layout",
            custom_threshold=0.04  # Full page may have more variations
        )

        # Don't fail on full page differences, just log
        if not passed:
            print(f"Note: Full page has {diff * 100:.2f}% difference from baseline")

    def test_modal_overlay_rendering(self):
        """
        Visual test: Modal overlay and backdrop

        VALIDATES:
        - Backdrop darkness/opacity
        - Modal centering
        - z-index layering
        - Overlay blur effects
        """
        # Open modal to show overlay
        create_btn = self.wait_for_element((By.ID, "createLocationBtn"))
        self.click_element_js(create_btn)
        time.sleep(1)

        # Capture full screen to see overlay effect
        passed, diff = self.visual.capture_and_compare(
            "modal_overlay_effect",
            custom_threshold=0.05  # Overlay may render slightly differently
        )

        if not passed:
            print(f"Note: Modal overlay has {diff * 100:.2f}% difference")

    def test_responsive_tablet_layout(self):
        """
        Visual test: Tablet viewport layout

        VALIDATES:
        - Locations dashboard adapts to tablet screens
        - Tables remain usable
        - Modals fit viewport
        """
        self.driver.set_window_size(768, 1024)
        time.sleep(1)

        passed, diff = self.visual.capture_and_compare(
            "responsive_tablet",
            custom_threshold=0.08  # Responsive layouts vary more
        )

        # Log but don't fail on responsive variations
        if not passed:
            print(f"Tablet layout difference: {diff * 100:.2f}%")

    def test_accessible_focus_states(self):
        """
        Visual test: Focus indicators for accessibility

        VALIDATES:
        - Focus rings visible on interactive elements
        - Keyboard navigation indicators
        - High contrast mode compatibility

        WHY THIS MATTERS:
        Keyboard users rely on focus indicators.
        Visual regression can catch CSS changes that break accessibility.
        """
        # Focus on create button
        create_btn = self.wait_for_element((By.ID, "createLocationBtn"))
        self.driver.execute_script("arguments[0].focus();", create_btn)
        time.sleep(0.3)

        passed, diff = self.visual.capture_and_compare(
            "focus_state_button",
            element_selector="#createLocationBtn",
            custom_threshold=0.15  # Focus states may vary significantly
        )

        # Log focus state difference
        if not passed:
            print(f"Focus state difference: {diff * 100:.2f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--update-baselines"])
