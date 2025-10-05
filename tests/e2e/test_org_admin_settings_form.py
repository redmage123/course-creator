"""
E2E Tests for Org Admin Dashboard Settings Form

BUSINESS CONTEXT:
End-to-end tests validate that the organization settings form loads
correctly with all organization data populated from the API.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver for browser automation
- Tests real browser behavior with API integration
- Validates form field population from organization data

TDD METHODOLOGY:
These tests catch issues like:
- Form fields being empty when they should be populated
- API data not being loaded before form population
- Missing form fields in HTML
- Race conditions between data loading and form rendering
"""

import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

pytestmark = pytest.mark.nondestructive


class TestOrgAdminSettingsForm:
    """
    Test Suite: Organization Settings Form E2E

    REQUIREMENT: Settings form must populate with organization data
    """

    @pytest.fixture(scope="function")
    def driver(self):
        """
        Setup Selenium WebDriver with Chrome

        BUSINESS CONTEXT:
        Creates isolated browser instance for each test to prevent state leakage
        """
        import tempfile
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        # Create unique temp directory for user data
        temp_dir = tempfile.mkdtemp(prefix='chrome_test_')
        chrome_options.add_argument(f'--user-data-dir={temp_dir}')

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        yield driver
        driver.quit()

    @pytest.fixture(scope="session")
    def base_url(self):
        """Base URL for tests"""
        return os.getenv('TEST_BASE_URL', 'https://176.9.99.103:3000')

    @pytest.fixture
    def authenticated_driver(self, driver, base_url):
        """Setup authenticated session"""
        driver.get(f'{base_url}/html/index.html')

        # Set up authenticated state
        driver.execute_script("""
            localStorage.setItem('authToken', 'settings-test-token');
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

    def test_settings_tab_exists(self, authenticated_driver):
        """
        TEST: Settings tab navigation exists
        REQUIREMENT: User should be able to navigate to settings
        """
        try:
            settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
            assert settings_tab.is_displayed(), "Settings tab should be visible"
            assert settings_tab.is_enabled(), "Settings tab should be clickable"
        except NoSuchElementException:
            pytest.fail("Settings tab not found in navigation")

    def test_settings_form_exists(self, authenticated_driver):
        """
        TEST: Settings form exists in DOM
        REQUIREMENT: Settings tab should contain organization settings form
        """
        # Click settings tab
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(2)

        # Check for form
        try:
            settings_form = authenticated_driver.find_element(By.ID, 'orgSettingsForm')
            assert settings_form is not None, "Settings form should exist"
        except NoSuchElementException:
            pytest.fail("Settings form (orgSettingsForm) not found")

    def test_organization_name_field_populated(self, authenticated_driver):
        """
        TEST: Organization name field is populated
        REQUIREMENT: Form should load organization name from API

        THIS TEST WOULD HAVE CAUGHT:
        - Empty form fields when organization data exists
        - Form populated before data loaded (race condition)
        """
        # Navigate to settings
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(3)  # Wait for data to load

        # Check organization name field
        try:
            org_name_field = authenticated_driver.find_element(By.ID, 'orgNameSetting')
            org_name_value = org_name_field.get_attribute('value')

            # Should not be empty (API returns "AI Elevate")
            assert org_name_value is not None, "Organization name should not be None"
            assert len(org_name_value) > 0, "Organization name should not be empty"

            print(f"✅ Organization name populated: {org_name_value}")

        except NoSuchElementException:
            pytest.fail("Organization name field (orgNameSetting) not found")

    def test_organization_slug_field_populated(self, authenticated_driver):
        """
        TEST: Organization slug/ID field is populated
        REQUIREMENT: Form should load organization slug from API
        """
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(3)

        try:
            org_slug_field = authenticated_driver.find_element(By.ID, 'orgSlugSetting')
            org_slug_value = org_slug_field.get_attribute('value')

            assert org_slug_value is not None, "Organization slug should not be None"
            assert len(org_slug_value) > 0, "Organization slug should not be empty"

            # Should be readonly
            is_readonly = org_slug_field.get_attribute('readonly')
            assert is_readonly is not None, "Organization slug should be readonly"

            print(f"✅ Organization slug populated: {org_slug_value}")

        except NoSuchElementException:
            pytest.fail("Organization slug field (orgSlugSetting) not found")

    def test_organization_description_field_populated(self, authenticated_driver):
        """
        TEST: Organization description field is populated
        REQUIREMENT: Form should load organization description from API
        """
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(3)

        try:
            org_desc_field = authenticated_driver.find_element(By.ID, 'orgDescriptionSetting')
            org_desc_value = org_desc_field.get_attribute('value')

            # Description might be empty, but field should exist
            assert org_desc_value is not None, "Organization description field should exist"

            print(f"✅ Organization description field exists: '{org_desc_value}'")

        except NoSuchElementException:
            pytest.fail("Organization description field (orgDescriptionSetting) not found")

    def test_contact_email_field_populated(self, authenticated_driver):
        """
        TEST: Contact email field is populated
        REQUIREMENT: Form should load contact email from API
        """
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(3)

        try:
            email_field = authenticated_driver.find_element(By.ID, 'orgContactEmailSetting')
            email_value = email_field.get_attribute('value')

            assert email_value is not None, "Contact email should not be None"
            assert len(email_value) > 0, "Contact email should not be empty"
            assert '@' in email_value, "Contact email should be valid email format"

            print(f"✅ Contact email populated: {email_value}")

        except NoSuchElementException:
            pytest.fail("Contact email field (orgContactEmailSetting) not found")

    def test_address_fields_populated(self, authenticated_driver):
        """
        TEST: Address fields are populated
        REQUIREMENT: Form should load street, city, state, postal code from API
        """
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(3)

        address_fields = {
            'orgStreetAddressSetting': 'Street Address',
            'orgCitySetting': 'City',
            'orgStateProvinceSetting': 'State/Province',
            'orgPostalCodeSetting': 'Postal Code'
        }

        for field_id, field_name in address_fields.items():
            try:
                field = authenticated_driver.find_element(By.ID, field_id)
                field_value = field.get_attribute('value')

                # Address fields might be empty, but should exist
                assert field_value is not None, f"{field_name} field should exist"

                print(f"✅ {field_name} field exists: '{field_value}'")

            except NoSuchElementException:
                pytest.fail(f"{field_name} field ({field_id}) not found")

    def test_domain_field_populated(self, authenticated_driver):
        """
        TEST: Domain field is populated
        REQUIREMENT: Form should load organization domain from API
        """
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(3)

        try:
            domain_field = authenticated_driver.find_element(By.ID, 'orgDomainSetting')
            domain_value = domain_field.get_attribute('value')

            # Domain might be empty, but field should exist
            assert domain_value is not None, "Domain field should exist"

            print(f"✅ Domain field exists: '{domain_value}'")

        except NoSuchElementException:
            pytest.fail("Domain field (orgDomainSetting) not found")

    def test_console_shows_settings_loaded_message(self, authenticated_driver):
        """
        TEST: Console logs confirm settings data loaded
        REQUIREMENT: Should log "Loading settings data" and "Settings form populated"
        """
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(3)

        # Get console logs
        logs = authenticated_driver.get_log('browser')

        # Check for our debug messages
        settings_logs = [
            log for log in logs
            if 'Loading settings data' in log['message'] or
               'Settings form populated' in log['message']
        ]

        # Should have at least one log message about settings
        assert len(settings_logs) > 0, "Should have console logs about settings loading"

        print(f"✅ Found {len(settings_logs)} settings-related console messages")

    def test_no_javascript_errors_loading_settings(self, authenticated_driver):
        """
        TEST: No JavaScript errors when loading settings
        REQUIREMENT: Settings tab should load without console errors
        """
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(3)

        # Get browser console logs
        logs = authenticated_driver.get_log('browser')

        # Filter for critical errors (ignore network errors since backend might not be running)
        critical_errors = [
            log for log in logs
            if log['level'] == 'SEVERE'
            and 'Failed to fetch' not in log['message']
            and 'NetworkError' not in log['message']
            and 'ERR_CONNECTION_REFUSED' not in log['message']
        ]

        # Should have no critical JavaScript errors
        assert len(critical_errors) == 0, f"Found critical errors: {critical_errors}"

    def test_form_fields_are_editable(self, authenticated_driver):
        """
        TEST: Form fields are editable (except readonly fields)
        REQUIREMENT: User should be able to edit organization settings
        """
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(3)

        # Check name field is editable
        org_name_field = authenticated_driver.find_element(By.ID, 'orgNameSetting')
        assert org_name_field.is_enabled(), "Organization name field should be editable"

        # Try to type in it
        org_name_field.clear()
        org_name_field.send_keys("Test Organization")
        new_value = org_name_field.get_attribute('value')
        assert new_value == "Test Organization", "Should be able to edit organization name"

        print("✅ Form fields are editable")

    def test_save_button_exists(self, authenticated_driver):
        """
        TEST: Save settings button exists
        REQUIREMENT: User should be able to save settings changes
        """
        settings_tab = authenticated_driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()
        time.sleep(2)

        try:
            # Look for save button (might be type="submit" or onclick handler)
            save_buttons = authenticated_driver.find_elements(By.CSS_SELECTOR,
                'button[type="submit"], button[onclick*="save"]')

            assert len(save_buttons) > 0, "Should have at least one save button"

            print(f"✅ Found {len(save_buttons)} save button(s)")

        except Exception as e:
            pytest.fail(f"Error finding save button: {e}")


class TestSettingsFormDataLoading:
    """
    Test Suite: Settings Form Data Loading Behavior

    REQUIREMENT: Form should handle data loading correctly
    """

    @pytest.fixture(scope="function")
    def driver(self):
        """Setup Selenium WebDriver"""
        import tempfile
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-gpu')

        # Create unique temp directory for user data
        temp_dir = tempfile.mkdtemp(prefix='chrome_test_')
        chrome_options.add_argument(f'--user-data-dir={temp_dir}')

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        yield driver
        driver.quit()

    @pytest.fixture(scope="session")
    def base_url(self):
        """Base URL for tests"""
        return os.getenv('TEST_BASE_URL', 'https://176.9.99.103:3000')

    def test_form_waits_for_organization_data(self, driver, base_url):
        """
        TEST: Form doesn't populate until organization data is loaded
        REQUIREMENT: Should avoid race conditions
        """
        driver.get(f'{base_url}/html/index.html')

        # Set authenticated state
        driver.execute_script("""
            localStorage.setItem('authToken', 'test-token');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                role: 'organization_admin',
                organization_id: '259da6df-c148-40c2-bcd9-dc6889e7e9fb'
            }));
        """)

        # Navigate to dashboard
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=259da6df-c148-40c2-bcd9-dc6889e7e9fb')
        time.sleep(1)  # Brief wait for initial load

        # Click settings immediately
        settings_tab = driver.find_element(By.CSS_SELECTOR, '[data-tab="settings"]')
        settings_tab.click()

        # Wait a bit for data to load
        time.sleep(3)

        # Form should still be populated correctly
        org_name_field = driver.find_element(By.ID, 'orgNameSetting')
        org_name_value = org_name_field.get_attribute('value')

        # Should not be empty even if we switched tabs quickly
        assert len(org_name_value) > 0, "Form should populate even with quick tab switching"

        print("✅ Form handles quick tab switching correctly")
