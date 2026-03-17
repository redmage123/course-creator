"""
E2E Test to PROVE Login Redirect Logic Works Correctly

Tests that:
1. Admin user redirects to site-admin-dashboard.html
2. Organization admin (bbrelin) redirects to org-admin-dashboard.html
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


class TestLoginRedirectProof:
    """Prove that login redirects work correctly for different user roles."""

    @classmethod
    def setup_class(cls):
        """Setup test environment and browser"""
        cls.config = SeleniumConfig()
        cls.base_url = cls.config.base_url

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
        """Clear localStorage, cookies, and cache before each test"""
        self.driver.get(f"{self.base_url}/")
        self.driver.execute_script("localStorage.clear();")
        self.driver.execute_script("sessionStorage.clear();")
        self.driver.delete_all_cookies()

        # Clear cache by navigating to a blank page then back
        self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
        time.sleep(1)

    def save_screenshot(self, name: str):
        """Take screenshot for debugging"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.screenshot_dir}/login_redirect_{name}_{timestamp}.png"
        self.driver.save_screenshot(filename)
        print(f"Screenshot saved: {filename}")

    def test_admin_login_redirects_to_site_admin_dashboard(self):
        """PROOF: Admin user redirects to site-admin-dashboard.html"""
        print("\n🔍 Testing admin login redirect...")

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")
        time.sleep(2)

        # Accept privacy modal if present
        try:
            privacy_modal = self.driver.find_element(By.ID, "privacyModal")
            if privacy_modal.is_displayed():
                accept_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
                accept_btn.click()
                time.sleep(0.5)
        except:
            pass

        # Click login button to show dropdown
        login_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        )
        login_btn.click()
        time.sleep(1)

        self.save_screenshot("01_login_dropdown_opened")

        # Wait for login dropdown menu to be visible
        login_menu = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "loginMenu"))
        )
        assert login_menu.is_displayed(), "Login dropdown menu should be visible"

        # Enter admin credentials
        email_field = self.driver.find_element(By.ID, "loginEmail")
        password_field = self.driver.find_element(By.ID, "loginPassword")

        email_field.clear()
        email_field.send_keys("admin")

        password_field.clear()
        password_field.send_keys("admin123!")

        self.save_screenshot("02_admin_credentials_entered")

        # Click sign in button
        signin_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Sign In')]")
        signin_btn.click()

        print("⏳ Waiting for redirect to site-admin-dashboard...")

        # Wait a bit for the request to complete
        time.sleep(2)

        # Check for any JavaScript errors
        logs = self.driver.get_log('browser')
        if logs:
            print("🐛 Browser console logs:")
            for log in logs:
                print(f"   {log['level']}: {log['message']}")

        # Check current URL
        current_url_before = self.driver.current_url
        print(f"📍 Current URL before redirect: {current_url_before}")

        # Check localStorage
        auth_token = self.driver.execute_script("return localStorage.getItem('authToken');")
        user_role = self.driver.execute_script("return localStorage.getItem('userRole');")
        print(f"🔑 Auth token exists: {auth_token is not None}")
        print(f"👤 User role: {user_role}")

        # Wait for redirect to site-admin dashboard
        try:
            WebDriverWait(self.driver, 15).until(
                EC.url_contains("site-admin-dashboard.html")
            )
        except:
            current_url_after = self.driver.current_url
            print(f"❌ Redirect failed. Current URL: {current_url_after}")
            self.save_screenshot("03_redirect_failed")
            raise

        current_url = self.driver.current_url
        print(f"✅ Redirected to: {current_url}")

        assert "site-admin-dashboard.html" in current_url, \
            f"Admin should redirect to site-admin-dashboard.html, but got: {current_url}"

        # Wait for dashboard to load
        time.sleep(3)

        self.save_screenshot("03_site_admin_dashboard_loaded")

        # Verify dashboard elements are present
        try:
            page_title = self.driver.find_element(By.TAG_NAME, "h1")
            print(f"📊 Dashboard title: {page_title.text}")
        except:
            print("⚠️  Could not find dashboard title")

        # Verify localStorage has correct role
        user_role = self.driver.execute_script("return localStorage.getItem('userRole');")
        print(f"👤 User role in localStorage: {user_role}")

        assert user_role in ["site_admin", "siteadmin"], \
            f"User role should be site_admin, but got: {user_role}"

        print("✅ PROOF COMPLETE: Admin login redirects to site-admin-dashboard.html")

    def test_org_admin_login_redirects_to_org_admin_dashboard(self):
        """PROOF: Organization admin (bbrelin) redirects to org-admin-dashboard.html"""
        print("\n🔍 Testing org admin (bbrelin) login redirect...")

        # Navigate to homepage
        self.driver.get(f"{self.base_url}/html/index.html")
        time.sleep(2)

        # Accept privacy modal if present
        try:
            privacy_modal = self.driver.find_element(By.ID, "privacyModal")
            if privacy_modal.is_displayed():
                accept_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
                accept_btn.click()
                time.sleep(0.5)
        except:
            pass

        # Click login button to show dropdown
        login_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        )
        login_btn.click()
        time.sleep(1)

        self.save_screenshot("04_login_dropdown_opened_for_bbrelin")

        # Wait for login dropdown menu to be visible
        login_menu = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "loginMenu"))
        )
        assert login_menu.is_displayed(), "Login dropdown menu should be visible"

        # Enter bbrelin credentials
        email_field = self.driver.find_element(By.ID, "loginEmail")
        password_field = self.driver.find_element(By.ID, "loginPassword")

        email_field.clear()
        email_field.send_keys("bbrelin")

        password_field.clear()
        password_field.send_keys("f00bar123!")

        self.save_screenshot("05_bbrelin_credentials_entered")

        # Click sign in button
        signin_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Sign In')]")
        signin_btn.click()

        print("⏳ Waiting for redirect to org-admin-dashboard...")

        # Wait for redirect to org-admin dashboard
        WebDriverWait(self.driver, 15).until(
            EC.url_contains("org-admin-dashboard.html")
        )

        current_url = self.driver.current_url
        print(f"✅ Redirected to: {current_url}")

        assert "org-admin-dashboard.html" in current_url, \
            f"Org admin should redirect to org-admin-dashboard.html, but got: {current_url}"

        # Verify org_id parameter is included
        assert "org_id=" in current_url, \
            f"Org admin redirect should include org_id parameter, but got: {current_url}"

        # Wait for dashboard to load
        time.sleep(3)

        self.save_screenshot("06_org_admin_dashboard_loaded")

        # Verify dashboard elements are present
        try:
            page_title = self.driver.find_element(By.TAG_NAME, "h1")
            print(f"📊 Dashboard title: {page_title.text}")
        except:
            print("⚠️  Could not find dashboard title")

        # Verify localStorage has correct role
        user_role = self.driver.execute_script("return localStorage.getItem('userRole');")
        print(f"👤 User role in localStorage: {user_role}")

        assert user_role in ["org_admin", "organization_admin", "orgadmin", "organizationadmin"], \
            f"User role should be org_admin, but got: {user_role}"

        print("✅ PROOF COMPLETE: Org admin (bbrelin) login redirects to org-admin-dashboard.html")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
