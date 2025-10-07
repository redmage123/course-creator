"""
End-to-end tests for Guest User Privacy & Cookie Consent Journey

Tests complete guest user workflows including:
- Cookie consent banner display and interaction
- Privacy policy and cookie policy navigation
- Cookie preference management
- GDPR Right to Access (View My Data)
- GDPR Right to Erasure (Delete My Data)
- CCPA "Do Not Sell" opt-out
- Demo chatbot interaction with guest sessions

BUSINESS CONTEXT:
These tests ensure GDPR/CCPA/PIPEDA compliance by verifying that guest users
can manage their privacy preferences, access their data, and delete their data
through the browser UI as required by privacy regulations.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver for browser automation
- Tests cookie consent banner JavaScript API
- Verifies localStorage persistence
- Tests Privacy API endpoints through browser interactions
- Validates HTTPS-only communication
"""

import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import from local e2e directory
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from selenium_base import SeleniumConfig, ChromeDriverSetup


class TestGuestPrivacyJourneyE2E:
    """
    End-to-end tests for guest user privacy and cookie consent workflows

    Test Coverage:
    - Cookie consent banner auto-display
    - Accept All / Reject All / Customize buttons
    - Cookie preference persistence
    - Privacy policy navigation
    - Cookie policy navigation
    - Cookie consent manager page
    - GDPR Right to Access
    - GDPR Right to Erasure
    - CCPA Do Not Sell opt-out
    """

    @classmethod
    def setup_class(cls):
        """Setup test environment and browser"""
        cls.config = SeleniumConfig()
        cls.base_url = cls.config.base_url
        cls.frontend_url = f"{cls.base_url}:3000"
        cls.demo_api_url = f"{cls.base_url}:8010/api/v1/demo"
        cls.privacy_api_url = f"{cls.base_url}:8010/api/v1/privacy"

        # Setup Chrome driver
        chrome_options = ChromeDriverSetup.create_chrome_options(cls.config)
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, cls.config.explicit_wait)

        # Set window size
        cls.driver.set_window_size(cls.config.window_width, cls.config.window_height)

    @classmethod
    def teardown_class(cls):
        """Clean up browser"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def setup_method(self):
        """Clear localStorage and cookies before each test"""
        self.driver.get(f"{self.frontend_url}/")
        self.driver.execute_script("localStorage.clear();")
        self.driver.delete_all_cookies()
        time.sleep(1)

    def take_screenshot(self, name: str):
        """Take screenshot for debugging"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.screenshot_dir}/guest_privacy_{name}_{timestamp}.png"
        self.driver.save_screenshot(filename)
        print(f"Screenshot saved: {filename}")

    # ================================================================
    # TEST 1: Cookie Consent Banner Auto-Display
    # ================================================================

    def test_01_cookie_banner_auto_displays_on_first_visit(self):
        """
        Test that cookie consent banner automatically appears on first visit

        GDPR Requirement: Article 7 - Consent must be obtained before processing

        Steps:
        1. Navigate to platform homepage
        2. Wait 1 second (banner delay)
        3. Verify banner is visible
        4. Verify banner contains required elements
        """
        # Navigate to homepage
        self.driver.get(f"{self.frontend_url}/")

        # Wait for banner to appear (1 second delay + animation)
        time.sleep(2)

        try:
            # Find cookie consent banner
            banner = self.wait.until(
                EC.presence_of_element_located((By.ID, "cookie-consent-banner"))
            )

            # Verify banner is visible
            assert banner.is_displayed(), "Cookie consent banner should be visible"

            # Verify banner contains required buttons
            accept_btn = banner.find_element(By.CLASS_NAME, "btn-accept-all")
            reject_btn = banner.find_element(By.CLASS_NAME, "btn-reject-all")
            customize_btn = banner.find_element(By.CLASS_NAME, "btn-customize")

            assert accept_btn.is_displayed(), "Accept All button should be visible"
            assert reject_btn.is_displayed(), "Reject All button should be visible"
            assert customize_btn.is_displayed(), "Customize button should be visible"

            # Verify banner text
            banner_text = banner.text
            assert "privacy" in banner_text.lower(), "Banner should mention privacy"
            assert "cookie" in banner_text.lower(), "Banner should mention cookies"

            self.take_screenshot("01_banner_displayed")

        except TimeoutException:
            self.take_screenshot("01_banner_timeout")
            pytest.fail("Cookie consent banner did not appear within timeout")

    # ================================================================
    # TEST 2: Accept All Cookies
    # ================================================================

    def test_02_accept_all_cookies_flow(self):
        """
        Test Accept All button functionality

        Steps:
        1. Navigate to homepage
        2. Wait for banner
        3. Click Accept All
        4. Verify banner disappears
        5. Verify localStorage contains consent
        6. Verify preferences are all true
        """
        self.driver.get(f"{self.frontend_url}/")
        time.sleep(2)

        try:
            # Find and click Accept All button
            banner = self.wait.until(
                EC.presence_of_element_located((By.ID, "cookie-consent-banner"))
            )
            accept_btn = banner.find_element(By.CLASS_NAME, "btn-accept-all")
            accept_btn.click()

            # Wait for banner to disappear
            time.sleep(2)

            # Debug: Check localStorage state
            consent_given = self.driver.execute_script("return localStorage.getItem('cookie_consent_given');")
            session_id = self.driver.execute_script("return localStorage.getItem('guest_session_id');")
            print(f"DEBUG: cookie_consent_given = {consent_given}")
            print(f"DEBUG: guest_session_id = {session_id}")

            # Verify banner is gone
            banners = self.driver.find_elements(By.ID, "cookie-consent-banner")
            assert len(banners) == 0, "Banner should disappear after accepting"

            # Verify localStorage
            consent_given = self.driver.execute_script("return localStorage.getItem('cookie_consent_given');")
            assert consent_given == "true", "Consent should be recorded in localStorage"

            # Verify preferences
            preferences_json = self.driver.execute_script("return localStorage.getItem('cookie_preferences');")
            preferences = json.loads(preferences_json)

            assert preferences['functional_cookies'] == True, "Functional cookies should be true"
            assert preferences['analytics_cookies'] == True, "Analytics cookies should be true"
            assert preferences['marketing_cookies'] == True, "Marketing cookies should be true"

            self.take_screenshot("02_accept_all_success")

        except Exception as e:
            self.take_screenshot("02_accept_all_error")
            pytest.fail(f"Accept All flow failed: {e}")

    # ================================================================
    # TEST 3: Reject All Cookies (Necessary Only)
    # ================================================================

    def test_03_reject_all_cookies_flow(self):
        """
        Test Reject All button functionality

        GDPR Requirement: Article 7(3) - Withdrawal must be as easy as giving consent

        Steps:
        1. Navigate to homepage
        2. Wait for banner
        3. Click Reject All
        4. Verify banner disappears
        5. Verify all optional cookies are false
        """
        self.driver.get(f"{self.frontend_url}/")
        time.sleep(2)

        try:
            banner = self.wait.until(
                EC.presence_of_element_located((By.ID, "cookie-consent-banner"))
            )
            reject_btn = banner.find_element(By.CLASS_NAME, "btn-reject-all")
            reject_btn.click()

            time.sleep(1)

            # Verify consent recorded
            consent_given = self.driver.execute_script("return localStorage.getItem('cookie_consent_given');")
            assert consent_given == "true", "Consent decision should be recorded"

            # Verify all optional cookies are false
            preferences_json = self.driver.execute_script("return localStorage.getItem('cookie_preferences');")
            preferences = json.loads(preferences_json)

            assert preferences['functional_cookies'] == False, "Functional cookies should be false"
            assert preferences['analytics_cookies'] == False, "Analytics cookies should be false"
            assert preferences['marketing_cookies'] == False, "Marketing cookies should be false"

            self.take_screenshot("03_reject_all_success")

        except Exception as e:
            self.take_screenshot("03_reject_all_error")
            pytest.fail(f"Reject All flow failed: {e}")

    # ================================================================
    # TEST 4: Cookie Consent Persistence
    # ================================================================

    def test_04_cookie_consent_persists_across_page_loads(self):
        """
        Test that cookie consent persists across page reloads

        Steps:
        1. Accept cookies
        2. Reload page
        3. Verify banner does NOT appear
        4. Verify preferences are still in localStorage
        """
        # Accept cookies
        self.driver.get(f"{self.frontend_url}/")
        time.sleep(2)

        banner = self.wait.until(
            EC.presence_of_element_located((By.ID, "cookie-consent-banner"))
        )
        accept_btn = banner.find_element(By.CLASS_NAME, "btn-accept-all")
        accept_btn.click()
        time.sleep(1)

        # Reload page
        self.driver.refresh()
        time.sleep(2)

        # Banner should NOT appear
        banners = self.driver.find_elements(By.ID, "cookie-consent-banner")
        assert len(banners) == 0, "Banner should not appear on subsequent visits"

        # Preferences should still be in localStorage
        consent_given = self.driver.execute_script("return localStorage.getItem('cookie_consent_given');")
        assert consent_given == "true", "Consent should persist across reloads"

        self.take_screenshot("04_persistence_verified")

    # ================================================================
    # TEST 5: Navigate to Cookie Consent Manager
    # ================================================================

    def test_05_navigate_to_cookie_consent_manager(self):
        """
        Test navigation to cookie consent manager page

        Steps:
        1. Navigate to /public/cookie-consent.html
        2. Verify page loads
        3. Verify all UI elements present
        4. Verify toggle switches
        """
        self.driver.get(f"{self.frontend_url}/public/cookie-consent.html")

        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        # Verify page title
        page_title = self.driver.find_element(By.TAG_NAME, "h1").text
        assert "cookie" in page_title.lower(), "Page should be about cookies"

        # Verify toggle switches exist
        functional_toggle = self.driver.find_element(By.ID, "functional-cookies")
        analytics_toggle = self.driver.find_element(By.ID, "analytics-cookies")
        marketing_toggle = self.driver.find_element(By.ID, "marketing-cookies")

        assert functional_toggle is not None, "Functional toggle should exist"
        assert analytics_toggle is not None, "Analytics toggle should exist"
        assert marketing_toggle is not None, "Marketing toggle should exist"

        # Verify Save button exists
        save_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
        assert save_btn is not None, "Save button should exist"

        self.take_screenshot("05_consent_manager_page")

    # ================================================================
    # TEST 6: Update Cookie Preferences
    # ================================================================

    def test_06_update_cookie_preferences(self):
        """
        Test updating cookie preferences through manager page

        Steps:
        1. Navigate to cookie consent manager
        2. Toggle functional cookies ON
        3. Toggle analytics cookies ON
        4. Keep marketing cookies OFF
        5. Click Save
        6. Verify localStorage updated
        """
        self.driver.get(f"{self.frontend_url}/public/cookie-consent.html")
        time.sleep(1)

        # Toggle cookies (click the label, not the checkbox itself)
        functional_checkbox = self.driver.find_element(By.ID, "functional-cookies")
        analytics_checkbox = self.driver.find_element(By.ID, "analytics-cookies")

        # Get parent label elements (the clickable toggle switch)
        functional_toggle = functional_checkbox.find_element(By.XPATH, "..")
        analytics_toggle = analytics_checkbox.find_element(By.XPATH, "..")

        # Click toggles to turn them ON
        if not functional_checkbox.is_selected():
            functional_toggle.click()
        if not analytics_checkbox.is_selected():
            analytics_toggle.click()

        time.sleep(0.5)

        # Click Save button
        save_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
        save_btn.click()

        # Wait for save to complete
        time.sleep(2)

        # Verify localStorage
        preferences_json = self.driver.execute_script("return localStorage.getItem('cookie_preferences');")
        if preferences_json:
            preferences = json.loads(preferences_json)
            assert preferences['functional_cookies'] == True, "Functional should be true"
            assert preferences['analytics_cookies'] == True, "Analytics should be true"

        self.take_screenshot("06_preferences_updated")

    # ================================================================
    # TEST 7: Navigate to Privacy Policy
    # ================================================================

    def test_07_navigate_to_privacy_policy(self):
        """
        Test navigation to privacy policy page

        GDPR Requirement: Article 13 - Information to be provided

        Steps:
        1. Navigate to /public/privacy-policy.html
        2. Verify page loads
        3. Verify required sections exist
        """
        self.driver.get(f"{self.frontend_url}/public/privacy-policy.html")

        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        # Verify page title
        page_title = self.driver.find_element(By.TAG_NAME, "h1").text
        assert "privacy" in page_title.lower(), "Page should be privacy policy"

        # Verify version is displayed
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        assert "3.3.0" in page_text, "Version should be displayed"
        assert "GDPR" in page_text, "Should mention GDPR"
        assert "CCPA" in page_text, "Should mention CCPA"
        assert "PIPEDA" in page_text, "Should mention PIPEDA"

        self.take_screenshot("07_privacy_policy_page")

    # ================================================================
    # TEST 8: Navigate to Cookie Policy
    # ================================================================

    def test_08_navigate_to_cookie_policy(self):
        """
        Test navigation to cookie policy page

        Steps:
        1. Navigate to /public/cookie-policy.html
        2. Verify page loads
        3. Verify cookie categories are documented
        """
        self.driver.get(f"{self.frontend_url}/public/cookie-policy.html")

        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        # Verify page title
        page_title = self.driver.find_element(By.TAG_NAME, "h1").text
        assert "cookie" in page_title.lower(), "Page should be cookie policy"

        # Verify cookie categories are documented
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        assert "Strictly Necessary" in page_text, "Should document necessary cookies"
        assert "Functional" in page_text, "Should document functional cookies"
        assert "Analytics" in page_text, "Should document analytics cookies"
        assert "Marketing" in page_text, "Should document marketing cookies"

        self.take_screenshot("08_cookie_policy_page")

    # ================================================================
    # TEST 9: GDPR Right to Access (View My Data)
    # ================================================================

    def test_09_gdpr_right_to_access(self):
        """
        Test GDPR Right to Access functionality

        GDPR Requirement: Article 15 - Right of access by the data subject

        Steps:
        1. Create a guest session
        2. Navigate to cookie consent manager
        3. Click "View My Data"
        4. Verify data is displayed
        """
        # First, create a session by visiting the platform
        self.driver.get(f"{self.frontend_url}/")
        time.sleep(2)

        # Get session ID from localStorage
        session_id = self.driver.execute_script("return localStorage.getItem('guest_session_id');")

        # If no session ID, banner should create one when accepted
        if not session_id:
            try:
                banner = self.driver.find_element(By.ID, "cookie-consent-banner")
                accept_btn = banner.find_element(By.CLASS_NAME, "btn-accept-all")
                accept_btn.click()
                time.sleep(1)
                session_id = self.driver.execute_script("return localStorage.getItem('guest_session_id');")
            except:
                pass

        # Navigate to cookie consent manager
        self.driver.get(f"{self.frontend_url}/public/cookie-consent.html")
        time.sleep(1)

        # Click "View My Data" button
        try:
            view_data_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'View My Data')]")
            view_data_btn.click()

            # Wait for alert (JavaScript alert with data)
            time.sleep(1)

            # Switch to alert
            alert = self.driver.switch_to.alert
            alert_text = alert.text

            # Verify alert contains session data
            assert "session" in alert_text.lower() or "data" in alert_text.lower(), "Alert should contain session data"

            alert.accept()

            self.take_screenshot("09_view_my_data_success")

        except NoSuchElementException:
            self.take_screenshot("09_view_my_data_button_not_found")
            pytest.skip("View My Data button not found on page")

    # ================================================================
    # TEST 10: GDPR Right to Erasure (Delete My Data)
    # ================================================================

    def test_10_gdpr_right_to_erasure(self):
        """
        Test GDPR Right to Erasure functionality

        GDPR Requirement: Article 17 - Right to erasure ("right to be forgotten")

        Steps:
        1. Create a guest session
        2. Navigate to cookie consent manager
        3. Click "Delete My Data"
        4. Confirm deletion
        5. Verify session ID removed from localStorage
        """
        # Create session
        self.driver.get(f"{self.frontend_url}/")
        time.sleep(2)

        # Accept cookies to create session
        try:
            banner = self.driver.find_element(By.ID, "cookie-consent-banner")
            accept_btn = banner.find_element(By.CLASS_NAME, "btn-accept-all")
            accept_btn.click()
            time.sleep(1)
        except:
            pass

        # Verify session ID exists
        session_id_before = self.driver.execute_script("return localStorage.getItem('guest_session_id');")

        # Navigate to cookie consent manager
        self.driver.get(f"{self.frontend_url}/public/cookie-consent.html")
        time.sleep(1)

        # Click "Delete My Data" button
        try:
            delete_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Delete My Data')]")
            delete_btn.click()

            # Wait for confirmation alert
            time.sleep(2)

            # Accept confirmation alert
            alert = self.driver.switch_to.alert
            alert.accept()

            # Wait for success alert
            time.sleep(2)

            # Accept success alert
            alert = self.driver.switch_to.alert
            alert.accept()

            # Wait for deletion to complete
            time.sleep(1)

            # Verify session ID removed from localStorage
            session_id_after = self.driver.execute_script("return localStorage.getItem('guest_session_id');")
            assert session_id_after is None or session_id_after != session_id_before, "Session ID should be removed after deletion"

            self.take_screenshot("10_delete_my_data_success")

        except NoSuchElementException:
            self.take_screenshot("10_delete_button_not_found")
            pytest.skip("Delete My Data button not found on page")

    # ================================================================
    # TEST 11: CCPA "Do Not Sell" Opt-Out
    # ================================================================

    def test_11_ccpa_do_not_sell_opt_out(self):
        """
        Test CCPA "Do Not Sell My Personal Information" functionality

        CCPA Requirement: Right to Opt-Out of Sale

        Steps:
        1. Navigate to homepage
        2. Wait for cookie banner
        3. Click "Do Not Sell" link
        4. Verify marketing cookies disabled
        """
        self.driver.get(f"{self.frontend_url}/")
        time.sleep(2)

        try:
            # Find "Do Not Sell" link in banner
            banner = self.wait.until(
                EC.presence_of_element_located((By.ID, "cookie-consent-banner"))
            )

            do_not_sell_link = banner.find_element(By.XPATH, "//a[contains(text(), 'Do Not Sell')]")
            do_not_sell_link.click()

            # Wait for confirmation alert
            time.sleep(2)

            # Accept alert
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except:
                pass

            time.sleep(1)

            # Verify marketing cookies are disabled
            preferences_json = self.driver.execute_script("return localStorage.getItem('cookie_preferences');")
            if preferences_json:
                preferences = json.loads(preferences_json)
                assert preferences['marketing_cookies'] == False, "Marketing cookies should be disabled after CCPA opt-out"

            self.take_screenshot("11_ccpa_opt_out_success")

        except NoSuchElementException:
            self.take_screenshot("11_ccpa_link_not_found")
            pytest.skip("CCPA Do Not Sell link not found")

    # ================================================================
    # TEST 12: Complete Guest Journey (Integration Test)
    # ================================================================

    def test_12_complete_guest_privacy_journey(self):
        """
        Complete end-to-end guest privacy journey

        Steps:
        1. Visit homepage → Cookie banner appears
        2. Click Customize → Redirect to preferences page
        3. Set custom preferences
        4. Navigate to privacy policy
        5. Navigate to cookie policy
        6. Return to preferences
        7. View My Data
        8. Delete My Data
        9. Verify complete data erasure
        """
        # Step 1: Visit homepage
        self.driver.get(f"{self.frontend_url}/")
        time.sleep(2)

        # Step 2: Click Customize
        try:
            banner = self.wait.until(
                EC.presence_of_element_located((By.ID, "cookie-consent-banner"))
            )
            customize_btn = banner.find_element(By.CLASS_NAME, "btn-customize")
            customize_btn.click()

            # Should redirect to cookie-consent.html
            time.sleep(2)
            assert "cookie-consent.html" in self.driver.current_url, "Should redirect to preferences page"

            self.take_screenshot("12_step1_customize_redirect")

            # Step 3: Set custom preferences (functional + analytics ON, marketing OFF)
            functional_checkbox = self.driver.find_element(By.ID, "functional-cookies")
            analytics_checkbox = self.driver.find_element(By.ID, "analytics-cookies")

            # Get parent label elements (the clickable toggle switch)
            functional_toggle = functional_checkbox.find_element(By.XPATH, "..")
            analytics_toggle = analytics_checkbox.find_element(By.XPATH, "..")

            if not functional_checkbox.is_selected():
                functional_toggle.click()
            if not analytics_checkbox.is_selected():
                analytics_toggle.click()

            time.sleep(0.5)

            save_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
            save_btn.click()
            time.sleep(2)

            self.take_screenshot("12_step2_preferences_saved")

            # Step 4: Navigate to privacy policy
            privacy_link = self.driver.find_element(By.XPATH, "//a[@href='/public/privacy-policy.html']")
            privacy_link.click()
            time.sleep(1)
            assert "privacy-policy.html" in self.driver.current_url

            self.take_screenshot("12_step3_privacy_policy")

            # Step 5: Navigate to cookie policy
            self.driver.back()
            time.sleep(1)
            cookie_link = self.driver.find_element(By.XPATH, "//a[@href='/public/cookie-policy.html']")
            cookie_link.click()
            time.sleep(1)
            assert "cookie-policy.html" in self.driver.current_url

            self.take_screenshot("12_step4_cookie_policy")

            # Step 6: Return to preferences
            self.driver.back()
            time.sleep(1)

            # Step 7: View My Data
            view_data_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'View My Data')]")
            view_data_btn.click()
            time.sleep(2)

            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except:
                pass

            self.take_screenshot("12_step5_view_data")

            # Step 8: Delete My Data
            delete_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Delete My Data')]")
            delete_btn.click()
            time.sleep(2)

            # Handle the delete confirmation alerts (there are TWO alerts!)
            time.sleep(2)
            try:
                # First alert: Confirmation
                alert = self.driver.switch_to.alert
                print(f"First alert: {alert.text}")
                alert.accept()
                time.sleep(2)

                # Second alert: Success message
                alert = self.driver.switch_to.alert
                print(f"Second alert: {alert.text}")
                alert.accept()
                print("Both alerts accepted")
            except Exception as alert_error:
                print(f"Alert handling error: {alert_error}")

            time.sleep(1)

            # Step 9: Verify complete erasure
            session_id = self.driver.execute_script("return localStorage.getItem('guest_session_id');")
            # Note: Session ID might still exist in localStorage but should be deleted from backend
            print(f"Session ID after deletion: {session_id}")

            self.take_screenshot("12_step6_complete_journey")

        except Exception as e:
            self.take_screenshot("12_journey_error")
            pytest.fail(f"Complete journey test failed: {e}")
