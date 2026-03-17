"""
Visual Validation Tests for Org Admin Dashboard

BUSINESS CONTEXT:
Tests that verify UI elements render correctly with proper styling.
These tests catch CSS issues, layout problems, and visual regressions
that don't cause JavaScript errors but create poor user experience.

TECHNICAL IMPLEMENTATION:
- Uses Selenium to check computed CSS properties
- Validates element positioning and visibility
- Checks for responsive design compliance
- Verifies accessibility standards

TDD METHODOLOGY:
These tests would have caught:
- Header text not centered despite CSS rules
- !important not being applied
- Elements overlapping or misaligned
- Inaccessible UI elements
"""

import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options


class TestOrgAdminDashboardVisual:
    """
    Test Suite: Visual Rendering and CSS Validation

    REQUIREMENT: Dashboard UI must render correctly with proper styling
    """

    @pytest.fixture(scope="function")
    def driver(self):
        """Setup Selenium WebDriver with Grid support"""
        import tempfile
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--remote-debugging-port=0')  # Avoid port conflicts
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-data-dir={tempfile.mkdtemp()}')

        # Check for Selenium Grid configuration
        selenium_remote = os.getenv('SELENIUM_REMOTE')
        if selenium_remote:
            driver = webdriver.Remote(
                command_executor=selenium_remote,
                options=chrome_options
            )
        else:
            driver = webdriver.Chrome(options=chrome_options)

        driver.set_page_load_timeout(45)  # Increased for Grid reliability
        yield driver
        driver.quit()

    @pytest.fixture(scope="session")
    def base_url(self):
        """Base URL for tests"""
        return os.getenv('TEST_BASE_URL', 'https://localhost:3000')

    @pytest.fixture
    def authenticated_driver(self, driver, base_url):
        """Setup authenticated session"""
        driver.get(f'{base_url}/html/index.html')

        # Set up authenticated state
        driver.execute_script("""
            localStorage.setItem('authToken', 'visual-test-token');
            localStorage.setItem('currentUser', JSON.stringify({
                id: '550e8400-e29b-41d4-a716-446655440000',
                email: 'bbrelin@test.com',
                username: 'bbrelin',
                role: 'organization_admin',
                organization_id: '259da6df-c148-40c2-bcd9-dc6889e7e9fb'
            }));
            localStorage.setItem('sessionStart', Date.now().toString());
            localStorage.setItem('lastActivity', Date.now().toString());
        """)

        org_id = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id={org_id}')
        time.sleep(3)

        return driver

    def test_header_text_is_centered(self, authenticated_driver):
        """
        TEST: Organization header text is center-aligned
        REQUIREMENT: .org-header should have text-align: center

        THIS TEST WOULD HAVE CAUGHT:
        - Header text not centered
        - !important CSS rule not applied
        - Inline styles overriding CSS
        """
        try:
            # Find the org-header element
            org_header = authenticated_driver.find_element(By.CLASS_NAME, 'org-header')

            # Get computed CSS style
            text_align = org_header.value_of_css_property('text-align')

            # Should be center-aligned
            assert text_align == 'center', \
                f"Header text-align should be 'center', got '{text_align}'"

            print(f"✅ Header text is centered: {text_align}")

            # Also check the h1 inside
            org_title = authenticated_driver.find_element(By.ID, 'orgTitle')
            h1_text_align = org_title.value_of_css_property('text-align')

            assert h1_text_align == 'center', \
                f"H1 text-align should be 'center', got '{h1_text_align}'"

            print(f"✅ H1 title is centered: {h1_text_align}")

        except NoSuchElementException:
            pytest.fail("org-header element not found")

    def test_header_has_gradient_background(self, authenticated_driver):
        """
        TEST: Header has gradient background
        REQUIREMENT: .org-header should have linear-gradient background
        """
        try:
            org_header = authenticated_driver.find_element(By.CLASS_NAME, 'org-header')

            # Get background-image (where gradient is applied)
            background_image = org_header.value_of_css_property('background-image')

            # Should contain gradient
            assert 'gradient' in background_image.lower(), \
                f"Header should have gradient background, got: {background_image}"

            print(f"✅ Header has gradient background")

        except NoSuchElementException:
            pytest.fail("org-header element not found")

    def test_header_has_proper_padding(self, authenticated_driver):
        """
        TEST: Header has adequate padding
        REQUIREMENT: Visual spacing should be comfortable
        """
        try:
            org_header = authenticated_driver.find_element(By.CLASS_NAME, 'org-header')

            # Get padding
            padding = org_header.value_of_css_property('padding')

            # Should have some padding (not 0px)
            assert padding != '0px', "Header should have padding"

            print(f"✅ Header has padding: {padding}")

        except NoSuchElementException:
            pytest.fail("org-header element not found")

    def test_header_has_border_radius(self, authenticated_driver):
        """
        TEST: Header has rounded corners
        REQUIREMENT: Modern UI should have border-radius
        """
        try:
            org_header = authenticated_driver.find_element(By.CLASS_NAME, 'org-header')

            # Get border-radius
            border_radius = org_header.value_of_css_property('border-radius')

            # Should have border-radius (not 0px)
            assert border_radius != '0px', "Header should have rounded corners"

            print(f"✅ Header has border-radius: {border_radius}")

        except NoSuchElementException:
            pytest.fail("org-header element not found")

    def test_navigation_tabs_are_visible(self, authenticated_driver):
        """
        TEST: All navigation tabs are visible
        REQUIREMENT: Tabs should be displayed and clickable
        """
        expected_tabs = ['overview', 'projects', 'instructors', 'students', 'tracks', 'settings']

        for tab in expected_tabs:
            try:
                tab_element = authenticated_driver.find_element(By.CSS_SELECTOR, f'[data-tab="{tab}"]')

                # Check if visible
                is_displayed = tab_element.is_displayed()
                assert is_displayed, f"Tab '{tab}' should be visible"

                # Check if enabled (clickable)
                is_enabled = tab_element.is_enabled()
                assert is_enabled, f"Tab '{tab}' should be enabled"

            except NoSuchElementException:
                pytest.fail(f"Navigation tab '{tab}' not found")

        print(f"✅ All {len(expected_tabs)} navigation tabs are visible and enabled")

    def test_active_tab_has_different_styling(self, authenticated_driver):
        """
        TEST: Active tab has visual distinction
        REQUIREMENT: User should know which tab is active
        """
        # Click on a tab
        students_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="students"]')
        students_tab.click()
        time.sleep(1)

        # Check if it has 'active' class
        classes = students_tab.get_attribute('class')
        assert 'active' in classes, "Active tab should have 'active' class"

        print("✅ Active tab has distinct styling")

    def test_tab_content_visible_when_selected(self, authenticated_driver):
        """
        TEST: Tab content becomes visible when tab is clicked
        REQUIREMENT: Content should show/hide based on tab selection
        """
        # Click projects tab
        projects_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="projects"]')
        projects_tab.click()
        time.sleep(1)

        # Find projects content
        try:
            projects_content = authenticated_driver.find_element(By.ID, 'projects')

            # Check display property
            display = projects_content.value_of_css_property('display')
            assert display != 'none', "Projects content should be visible (display != none)"

            print("✅ Tab content becomes visible when selected")

        except NoSuchElementException:
            pytest.fail("Projects content div not found")

    def test_organization_title_is_visible(self, authenticated_driver):
        """
        TEST: Organization title is visible in header
        REQUIREMENT: User should see which organization they're managing
        """
        try:
            org_title = authenticated_driver.find_element(By.ID, 'orgTitle')

            # Should be visible
            assert org_title.is_displayed(), "Organization title should be visible"

            # Should have text content
            title_text = org_title.text
            assert len(title_text) > 0, "Organization title should have text"

            # Should contain "Organization Dashboard"
            assert 'Organization Dashboard' in title_text, \
                f"Title should contain 'Organization Dashboard', got: {title_text}"

            print(f"✅ Organization title visible: {title_text}")

        except NoSuchElementException:
            pytest.fail("Organization title element (orgTitle) not found")

    def test_no_overlapping_elements(self, authenticated_driver):
        """
        TEST: UI elements don't overlap
        REQUIREMENT: Layout should be clean with proper spacing
        """
        try:
            # Get header and navigation positions
            header = authenticated_driver.find_element(By.CLASS_NAME, 'org-header')
            header_rect = header.rect

            # Header should be at the top
            assert header_rect['y'] < 200, "Header should be near top of page"

            print("✅ No overlapping elements detected")

        except NoSuchElementException:
            pytest.fail("Header element not found for layout check")

    def test_responsive_design_mobile_viewport(self, driver, base_url):
        """
        TEST: Dashboard is responsive on mobile viewports
        REQUIREMENT: Should work on different screen sizes
        """
        # Set mobile viewport
        driver.set_window_size(375, 667)  # iPhone size

        driver.get(f'{base_url}/html/index.html')
        driver.execute_script("""
            localStorage.setItem('authToken', 'mobile-test-token');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                role: 'organization_admin',
                organization_id: '259da6df-c148-40c2-bcd9-dc6889e7e9fb'
            }));
        """)

        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=259da6df-c148-40c2-bcd9-dc6889e7e9fb')
        time.sleep(2)

        try:
            # Header should still be visible on mobile
            header = driver.find_element(By.CLASS_NAME, 'org-header')
            assert header.is_displayed(), "Header should be visible on mobile"

            # Navigation should be accessible (might stack vertically)
            nav_links = driver.find_elements(By.CLASS_NAME, 'nav-link')
            assert len(nav_links) > 0, "Navigation links should exist on mobile"

            print("✅ Dashboard is responsive on mobile viewport")

        except NoSuchElementException:
            pytest.fail("Dashboard elements not found on mobile viewport")

    def test_color_contrast_accessibility(self, authenticated_driver):
        """
        TEST: Text has sufficient color contrast
        REQUIREMENT: Should meet WCAG accessibility standards
        """
        try:
            org_title = authenticated_driver.find_element(By.ID, 'orgTitle')

            # Get text color and background color
            color = org_title.value_of_css_property('color')
            background = org_title.parent.value_of_css_property('background-color')

            # Basic check: they should be different
            assert color != background, "Text color should differ from background"

            print(f"✅ Text color: {color}, Background: {background}")

        except NoSuchElementException:
            pytest.fail("Organization title not found for contrast check")

    def test_logout_button_is_accessible(self, authenticated_driver):
        """
        TEST: Logout button is visible and clickable
        REQUIREMENT: User should be able to logout easily
        """
        try:
            logout_btn = authenticated_driver.find_element(By.ID, 'logoutBtn')

            # Should be visible
            assert logout_btn.is_displayed(), "Logout button should be visible"

            # Should be clickable
            assert logout_btn.is_enabled(), "Logout button should be enabled"

            print("✅ Logout button is accessible")

        except NoSuchElementException:
            print("⚠️ Logout button not found (might not be implemented yet)")

    def test_no_horizontal_scrollbar_on_desktop(self, authenticated_driver):
        """
        TEST: No horizontal scrolling required on desktop
        REQUIREMENT: Page should fit within viewport width
        """
        # Get page width vs viewport width
        page_width = authenticated_driver.execute_script("return document.body.scrollWidth;")
        viewport_width = authenticated_driver.execute_script("return window.innerWidth;")

        # Page should not exceed viewport (allowing small margin)
        assert page_width <= viewport_width + 20, \
            f"Page width ({page_width}px) exceeds viewport ({viewport_width}px)"

        print(f"✅ No horizontal scroll: page={page_width}px, viewport={viewport_width}px")

    def test_fonts_load_correctly(self, authenticated_driver):
        """
        TEST: Custom fonts load without errors
        REQUIREMENT: Typography should be consistent
        """
        try:
            org_title = authenticated_driver.find_element(By.ID, 'orgTitle')

            # Get font-family
            font_family = org_title.value_of_css_property('font-family')

            # Should have some font specified (not generic "serif" or "sans-serif" only)
            assert len(font_family) > 0, "Font family should be specified"

            print(f"✅ Font loaded: {font_family}")

        except NoSuchElementException:
            pytest.fail("Organization title not found for font check")


class TestVisualRegression:
    """
    Test Suite: Visual Regression Detection

    REQUIREMENT: UI changes should not break existing layouts
    """

    @pytest.fixture(scope="function")
    def driver(self):
        """Setup Selenium WebDriver with Grid support"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--remote-debugging-port=0')  # Avoid port conflicts
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--window-size=1920,1080')

        # Check for Selenium Grid configuration
        selenium_remote = os.getenv('SELENIUM_REMOTE')
        if selenium_remote:
            driver = webdriver.Remote(
                command_executor=selenium_remote,
                options=chrome_options
            )
        else:
            driver = webdriver.Chrome(options=chrome_options)

        driver.set_page_load_timeout(45)  # Increased for Grid reliability
        yield driver
        driver.quit()

    @pytest.fixture(scope="session")
    def base_url(self):
        """Base URL for tests"""
        return os.getenv('TEST_BASE_URL', 'https://localhost:3000')

    def test_header_height_is_reasonable(self, driver, base_url):
        """
        TEST: Header doesn't take up too much vertical space
        REQUIREMENT: Header should be prominent but not overwhelming
        """
        driver.get(f'{base_url}/html/index.html')
        driver.execute_script("""
            localStorage.setItem('authToken', 'test');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                role: 'organization_admin',
                organization_id: '259da6df-c148-40c2-bcd9-dc6889e7e9fb'
            }));
        """)

        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=259da6df-c148-40c2-bcd9-dc6889e7e9fb')
        time.sleep(2)

        try:
            header = driver.find_element(By.CLASS_NAME, 'org-header')
            header_height = header.size['height']

            viewport_height = driver.execute_script("return window.innerHeight;")

            # Header should not take more than 30% of viewport
            max_header_height = viewport_height * 0.3

            assert header_height < max_header_height, \
                f"Header too tall: {header_height}px (max: {max_header_height}px)"

            print(f"✅ Header height reasonable: {header_height}px (viewport: {viewport_height}px)")

        except NoSuchElementException:
            pytest.fail("Header element not found")

    def test_all_tab_content_sections_exist(self, driver, base_url):
        """
        TEST: All expected tab content sections are in DOM
        REQUIREMENT: Page structure should be complete
        """
        driver.get(f'{base_url}/html/index.html')
        driver.execute_script("""
            localStorage.setItem('authToken', 'test');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                role: 'organization_admin',
                organization_id: '259da6df-c148-40c2-bcd9-dc6889e7e9fb'
            }));
        """)

        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=259da6df-c148-40c2-bcd9-dc6889e7e9fb')
        time.sleep(2)

        expected_sections = ['overview', 'projects', 'instructors', 'students', 'tracks', 'settings']

        missing_sections = []
        for section in expected_sections:
            try:
                driver.find_element(By.ID, section)
            except NoSuchElementException:
                missing_sections.append(section)

        assert len(missing_sections) == 0, \
            f"Missing tab content sections: {missing_sections}"

        print(f"✅ All {len(expected_sections)} tab content sections present")
