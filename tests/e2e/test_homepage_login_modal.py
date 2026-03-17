"""
E2E Tests for Homepage Login Modal and Privacy Consent

Tests the new guest-first login modal system on the homepage:
- Login modal opens when Login button clicked
- Guest login is primary option
- Privacy consent modal appears on first visit
- Authentication flow works correctly
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import from local e2e directory
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from selenium_base import SeleniumConfig, ChromeDriverSetup


class TestHomepageLoginModal:
    """Test suite for homepage login modal and privacy consent functionality."""

    @classmethod
    def setup_class(cls):
        """Setup test environment and browser"""
        cls.config = SeleniumConfig()
        cls.base_url = cls.config.base_url

        # Setup Chrome driver without user-data-dir to avoid conflicts
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
        self.driver.get(f"{self.base_url}/")
        self.driver.execute_script("localStorage.clear();")
        self.driver.delete_all_cookies()
        time.sleep(1)

    def save_screenshot(self, name: str):
        """Take screenshot for debugging"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.screenshot_dir}/homepage_login_{name}_{timestamp}.png"
        self.driver.save_screenshot(filename)
        print(f"Screenshot saved: {filename}")

    def test_privacy_modal_appears_on_first_visit(self):
        """Test that privacy consent modal appears on first visit."""
        # Clear localStorage to simulate first visit
        self.driver.execute_script("localStorage.clear();")

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Wait for privacy modal to appear (1 second delay in code)
        time.sleep(1.5)

        privacy_modal = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "privacyModal"))
        )

        # Verify modal is visible
        assert privacy_modal.is_displayed(), "Privacy modal should be visible on first visit"

        # Verify modal content
        modal_title = self.driver.find_element(By.ID, "privacyModalTitle")
        assert "Privacy" in modal_title.text, "Privacy modal should have correct title"

        # Take screenshot
        self.save_screenshot("privacy_modal_first_visit")

    def test_privacy_modal_has_correct_options(self):
        """Test that privacy modal has all required options."""
        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Wait for privacy modal
        time.sleep(1.5)

        # Check for essential cookies (required)
        essential_checkbox = self.driver.find_element(By.ID, "essentialCookies")
        assert essential_checkbox.is_selected(), "Essential cookies should be checked"
        assert not essential_checkbox.is_enabled(), "Essential cookies should be disabled (required)"

        # Check for analytics cookies (optional)
        analytics_checkbox = self.driver.find_element(By.ID, "analyticsCookies")
        assert not analytics_checkbox.is_selected(), "Analytics cookies should not be checked by default"
        assert analytics_checkbox.is_enabled(), "Analytics cookies should be enabled (optional)"

        # Verify buttons exist
        accept_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
        reject_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Reject Optional')]")

        assert accept_btn.is_displayed(), "Accept All button should be visible"
        assert reject_btn.is_displayed(), "Reject Optional button should be visible"

        # Take screenshot
        self.save_screenshot("privacy_modal_options")

    def test_privacy_modal_accept_all(self):
        """Test accepting all cookies in privacy modal."""
        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Wait for privacy modal
        time.sleep(1.5)

        # Click Accept All
        accept_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
        accept_btn.click()

        # Wait for modal to close
        time.sleep(0.5)

        # Verify modal is closed
        privacy_modal = self.driver.find_element(By.ID, "privacyModal")
        assert not privacy_modal.is_displayed(), "Privacy modal should be closed after accepting"

        # Verify localStorage has consent
        consent = self.driver.execute_script("return localStorage.getItem('privacyConsent');")
        assert consent is not None, "Privacy consent should be stored"

        # Verify consent includes analytics
        import json
        consent_data = json.loads(consent)
        assert consent_data['analytics'] == True, "Analytics should be accepted"

        # Take screenshot
        self.save_screenshot("privacy_modal_accepted")

    def test_privacy_modal_reject_optional(self):
        """Test rejecting optional cookies in privacy modal."""
        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Wait for privacy modal
        time.sleep(1.5)

        # Click Reject Optional
        reject_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Reject Optional')]")
        reject_btn.click()

        # Wait for modal to close
        time.sleep(0.5)

        # Verify localStorage has consent
        consent = self.driver.execute_script("return localStorage.getItem('privacyConsent');")
        assert consent is not None, "Privacy consent should be stored"

        # Verify consent excludes analytics
        import json
        consent_data = json.loads(consent)
        assert consent_data['analytics'] == False, "Analytics should be rejected"

        # Take screenshot
        self.save_screenshot("privacy_modal_rejected")

    def test_login_button_opens_modal(self):
        """Test that clicking Login button opens modal instead of redirecting."""
        # Accept privacy first
        self.driver.execute_script("localStorage.setItem('privacyConsent', JSON.stringify({essential: true, analytics: false}));")

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Click Login button in header
        login_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        )
        login_btn.click()

        # Wait for login modal to appear
        login_modal = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "loginModal"))
        )

        # Verify modal is visible
        assert login_modal.is_displayed(), "Login modal should be visible after clicking Login"

        # Verify URL didn't change (modal, not redirect)
        assert "student-login.html" not in self.driver.current_url, "Should not redirect to login page"

        # Take screenshot
        self.save_screenshot("login_modal_opened")

    def test_login_modal_has_guest_option_primary(self):
        """Test that guest login is the primary/prominent option."""
        # Accept privacy first
        self.driver.execute_script("localStorage.setItem('privacyConsent', JSON.stringify({essential: true, analytics: false}));")

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Open login modal
        login_btn = self.driver.find_element(By.ID, "loginBtn")
        login_btn.click()

        # Wait for modal
        time.sleep(0.5)

        # Verify guest login button exists and is prominent
        guest_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continue as Guest')]")
        assert guest_btn.is_displayed(), "Guest login button should be visible"

        # Verify guest login is styled as primary button
        guest_btn_classes = guest_btn.get_attribute("class")
        assert "hero-btn-primary" in guest_btn_classes, "Guest login should be primary button style"

        # Verify description text
        guest_description = self.driver.find_element(By.CLASS_NAME, "guest-login-description")
        assert "Explore courses" in guest_description.text, "Guest login description should be present"

        # Take screenshot
        self.save_screenshot("login_modal_guest_primary")

    def test_login_modal_has_account_login_secondary(self):
        """Test that account login is secondary option."""
        # Accept privacy first
        self.driver.execute_script("localStorage.setItem('privacyConsent', JSON.stringify({essential: true, analytics: false}));")

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Open login modal
        login_btn = self.driver.find_element(By.ID, "loginBtn")
        login_btn.click()

        # Wait for modal
        time.sleep(0.5)

        # Verify divider exists
        divider = self.driver.find_element(By.CLASS_NAME, "modal-divider")
        assert divider.is_displayed(), "Divider should separate guest and account login"
        assert "or sign in" in divider.text.lower(), "Divider should have appropriate text"

        # Verify email field
        email_field = self.driver.find_element(By.ID, "loginEmail")
        assert email_field.is_displayed(), "Email field should be present"

        # Verify password field
        password_field = self.driver.find_element(By.ID, "loginPassword")
        assert password_field.is_displayed(), "Password field should be present"

        # Verify sign in button is secondary style
        signin_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Sign In')]")
        signin_btn_classes = signin_btn.get_attribute("class")
        assert "hero-btn-secondary" in signin_btn_classes, "Sign in should be secondary button style"

        # Take screenshot
        self.save_screenshot("login_modal_account_secondary")

    def test_login_modal_can_close(self):
        """Test that login modal can be closed."""
        # Accept privacy first
        self.driver.execute_script("localStorage.setItem('privacyConsent', JSON.stringify({essential: true, analytics: false}));")

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Open login modal
        login_btn = self.driver.find_element(By.ID, "loginBtn")
        login_btn.click()

        # Wait for modal
        time.sleep(0.5)

        # Click close button
        close_btn = self.driver.find_element(By.XPATH, "//button[@aria-label='Close modal']")
        close_btn.click()

        # Wait for modal to close
        time.sleep(0.5)

        # Verify modal is closed
        login_modal = self.driver.find_element(By.ID, "loginModal")
        assert not login_modal.is_displayed(), "Login modal should be closed after clicking X"

        # Take screenshot
        self.save_screenshot("login_modal_closed")

    def test_guest_login_redirects_correctly(self):
        """Test that guest login sets correct localStorage and redirects."""
        # Accept privacy first
        self.driver.execute_script("localStorage.setItem('privacyConsent', JSON.stringify({essential: true, analytics: false}));")

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Open login modal
        login_btn = self.driver.find_element(By.ID, "loginBtn")
        login_btn.click()

        # Wait for modal
        time.sleep(0.5)

        # Click guest login
        guest_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continue as Guest')]")
        guest_btn.click()

        # Wait for redirect
        time.sleep(2)

        # Verify redirect to student dashboard with guest parameter
        assert "student-dashboard.html" in self.driver.current_url, "Should redirect to student dashboard"
        assert "guest=true" in self.driver.current_url, "URL should have guest parameter"

        # Verify localStorage
        user_role = self.driver.execute_script("return localStorage.getItem('userRole');")
        is_guest = self.driver.execute_script("return localStorage.getItem('isGuest');")

        assert user_role == "guest", "User role should be guest"
        assert is_guest == "true", "isGuest should be true"

        # Take screenshot
        self.save_screenshot("guest_login_redirect")

    def test_login_modal_form_validation(self):
        """Test that login form has proper validation."""
        # Accept privacy first
        self.driver.execute_script("localStorage.setItem('privacyConsent', JSON.stringify({essential: true, analytics: false}));")

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Open login modal
        login_btn = self.driver.find_element(By.ID, "loginBtn")
        login_btn.click()

        # Wait for modal
        time.sleep(0.5)

        # Try to submit empty form
        signin_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Sign In')]")
        signin_btn.click()

        # Verify email field is required
        email_field = self.driver.find_element(By.ID, "loginEmail")
        assert email_field.get_attribute("required") is not None, "Email field should be required"

        # Enter invalid email
        email_field.send_keys("invalid-email")
        signin_btn.click()

        # HTML5 validation should prevent submission
        # (Browser will show validation message)

        # Enter valid email
        email_field.clear()
        email_field.send_keys("test@example.com")

        # Password field should also be required
        password_field = self.driver.find_element(By.ID, "loginPassword")
        assert password_field.get_attribute("required") is not None, "Password field should be required"

        # Take screenshot
        self.save_screenshot("login_modal_validation")

    def test_privacy_not_shown_on_subsequent_visits(self):
        """Test that privacy modal doesn't appear on subsequent visits."""
        # Set privacy consent (simulating previous visit)
        self.driver.execute_script("""
            localStorage.setItem('privacyConsent', JSON.stringify({
                essential: true,
                analytics: true,
                timestamp: new Date().toISOString()
            }));
        """)

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")

        # Wait 2 seconds (privacy modal shows after 1 second)
        time.sleep(2)

        # Verify privacy modal is NOT visible
        privacy_modal = self.driver.find_element(By.ID, "privacyModal")
        assert not privacy_modal.is_displayed(), "Privacy modal should not appear on subsequent visits"

        # Take screenshot
        self.save_screenshot("privacy_not_shown_again")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
