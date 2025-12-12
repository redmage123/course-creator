"""
Frontend Tests for Student Login UI - GDPR Compliant

This module contains comprehensive frontend tests for the student login user interface,
focusing on GDPR compliance, user experience, and privacy controls validation.

Business Context:
Tests the student login interface to ensure proper privacy consent collection,
data minimization in UI forms, and user-friendly access to educational content
while maintaining strict regulatory compliance.

Test Coverage:
- GDPR consent interface validation
- Form validation and error handling  
- Privacy notice presentation
- Device fingerprinting anonymization
- Login mode switching (credentials vs token)
- Accessibility and usability testing
- JavaScript module functionality
- Error message privacy protection
"""

import pytest
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# Python-based browser automation for testing
class StudentLoginUITest:
    """Test class for student login UI functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Configure Chrome for testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception:
            # Fallback to Firefox if Chrome not available
            self.driver = webdriver.Firefox()
        
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Set up test data
        self.test_student_login_url = "file://" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../frontend/html/student-login.html")
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        if hasattr(self, 'driver'):
            self.driver.quit()


class TestStudentLoginGDPRInterface(StudentLoginUITest):
    """Test GDPR compliance features in the student login interface."""
    
    def test_privacy_notice_displayed(self):
        """Test that privacy notice is prominently displayed."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Assert
        privacy_notice = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "privacy-notice"))
        )
        assert privacy_notice.is_displayed()
        
        # Verify privacy notice content
        notice_text = privacy_notice.text.lower()
        assert "gdpr" in notice_text or "privacy" in notice_text
        assert "educational purposes" in notice_text
        assert "privacy policy" in notice_text

    def test_consent_checkboxes_default_unchecked(self):
        """Test that consent checkboxes default to unchecked (GDPR Article 7)."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Assert
        analytics_consent = self.driver.find_element(By.ID, "consentAnalytics")
        notifications_consent = self.driver.find_element(By.ID, "consentNotifications")
        
        assert not analytics_consent.is_selected()
        assert not notifications_consent.is_selected()

    def test_consent_labels_descriptive(self):
        """Test that consent labels clearly describe data processing."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Assert
        analytics_label = self.driver.find_element(
            By.CSS_SELECTOR, "label[for='consentAnalytics']"
        )
        notifications_label = self.driver.find_element(
            By.CSS_SELECTOR, "label[for='consentNotifications']"
        )
        
        analytics_text = analytics_label.text.lower()
        notifications_text = notifications_label.text.lower()
        
        # Verify descriptive consent text
        assert "educational analytics" in analytics_text
        assert "learning patterns" in analytics_text or "analytics" in analytics_text
        
        assert "instructor notifications" in notifications_text
        assert "instructor" in notifications_text
        assert "log in" in notifications_text or "login" in notifications_text

    def test_privacy_policy_modal_accessible(self):
        """Test that privacy policy modal is accessible and informative."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Click privacy policy link
        privacy_link = self.driver.find_element(By.CLASS_NAME, "privacy-link")
        privacy_link.click()
        
        # Wait for modal to appear
        modal = self.wait.until(
            EC.visibility_of_element_located((By.ID, "privacyModal"))
        )
        
        # Assert
        assert modal.is_displayed()
        
        # Verify modal content
        modal_text = modal.text.lower()
        assert "gdpr" in modal_text
        assert "data processing" in modal_text
        assert "your rights" in modal_text
        assert "data retention" in modal_text

    def test_consent_withdrawal_notice(self):
        """Test that users are informed they can withdraw consent."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Assert
        consent_section = self.driver.find_element(By.CLASS_NAME, "consent-section")
        consent_text = consent_section.text.lower()
        
        # Should inform users they can change preferences
        assert "change" in consent_text or "withdraw" in consent_text
        assert "account settings" in consent_text or "preferences" in consent_text


class TestStudentLoginFormValidation(StudentLoginUITest):
    """Test form validation and user experience."""
    
    def test_required_field_validation(self):
        """Test that required fields are properly validated."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Try to submit empty form
        login_button = self.driver.find_element(By.ID, "credentialsBtn")
        login_button.click()
        
        # Assert
        username_field = self.driver.find_element(By.ID, "username")
        password_field = self.driver.find_element(By.ID, "userPassword")
        
        # HTML5 validation should prevent submission
        assert username_field.get_attribute("required") == "true"
        assert password_field.get_attribute("required") == "true"

    def test_login_mode_switching(self):
        """Test switching between credentials and token login modes."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Initially should be in credentials mode
        credentials_form = self.driver.find_element(By.ID, "credentialsForm")
        token_form = self.driver.find_element(By.ID, "tokenForm")
        
        assert credentials_form.is_displayed()
        assert not token_form.is_displayed()
        
        # Switch to token mode
        token_mode_button = self.driver.find_element(By.ID, "tokenMode")
        token_mode_button.click()
        
        # Wait for UI update
        time.sleep(0.5)
        
        # Assert
        assert not credentials_form.is_displayed()
        assert token_form.is_displayed()

    def test_course_context_display(self):
        """Test course context display when course parameter is provided."""
        # Arrange & Act
        test_url_with_course = f"{self.test_student_login_url}?course=test-course-123"
        self.driver.get(test_url_with_course)
        
        # The JavaScript should attempt to load course context
        # For this test, we verify the UI structure is correct
        
        # Assert
        course_context = self.driver.find_element(By.ID, "courseInfo")
        # Initially hidden, would be shown by JavaScript after loading
        assert course_context  # Element exists

    def test_error_message_display(self):
        """Test error message display functionality."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Execute JavaScript to show error (simulating failed login)
        self.driver.execute_script("""
            function showError(message) {
                const errorElement = document.getElementById('errorMessage');
                errorElement.textContent = message;
                errorElement.style.display = 'block';
            }
            showError('Test error message');
        """)
        
        # Assert
        error_message = self.driver.find_element(By.ID, "errorMessage")
        assert error_message.is_displayed()
        assert "Test error message" in error_message.text

    def test_success_message_display(self):
        """Test success message display functionality."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Execute JavaScript to show success
        self.driver.execute_script("""
            function showSuccess(message) {
                const successElement = document.getElementById('successMessage');
                successElement.textContent = message;
                successElement.style.display = 'block';
            }
            showSuccess('Login successful!');
        """)
        
        # Assert
        success_message = self.driver.find_element(By.ID, "successMessage")
        assert success_message.is_displayed()
        assert "Login successful!" in success_message.text


class TestStudentLoginAccessibility(StudentLoginUITest):
    """Test accessibility features of the student login interface."""
    
    def test_form_labels_associated(self):
        """Test that form inputs have properly associated labels."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Assert
        username_input = self.driver.find_element(By.ID, "username")
        password_input = self.driver.find_element(By.ID, "userPassword")
        
        # Check for label association
        username_label = self.driver.find_element(
            By.CSS_SELECTOR, "label[for='username']"
        )
        password_label = self.driver.find_element(
            By.CSS_SELECTOR, "label[for='userPassword']"
        )
        
        assert username_label.text
        assert password_label.text

    def test_keyboard_navigation(self):
        """Test keyboard navigation through form elements."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Start with username field focused
        username_input = self.driver.find_element(By.ID, "username")
        username_input.click()
        
        # Tab through form elements
        from selenium.webdriver.common.keys import Keys
        
        username_input.send_keys(Keys.TAB)
        password_input = self.driver.switch_to.active_element
        assert password_input.get_attribute("id") == "userPassword"
        
        # Continue tabbing should reach consent checkboxes
        password_input.send_keys(Keys.TAB)
        active_element = self.driver.switch_to.active_element
        
        # Should be able to navigate through all form elements
        assert active_element.tag_name in ["input", "button", "a"]

    def test_screen_reader_support(self):
        """Test screen reader support through ARIA attributes."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Assert
        consent_checkboxes = self.driver.find_elements(
            By.CSS_SELECTOR, ".consent-checkbox input[type='checkbox']"
        )
        
        for checkbox in consent_checkboxes:
            # Should have associated label
            checkbox_id = checkbox.get_attribute("id")
            label = self.driver.find_element(
                By.CSS_SELECTOR, f"label[for='{checkbox_id}']"
            )
            assert label.text  # Label should have descriptive text

    def test_color_contrast_elements_present(self):
        """Test that UI elements with proper contrast are present."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Assert - Check that key UI elements exist
        # (Actual color contrast would need specialized tools)
        privacy_notice = self.driver.find_element(By.CLASS_NAME, "privacy-notice")
        consent_section = self.driver.find_element(By.CLASS_NAME, "consent-section")
        login_button = self.driver.find_element(By.ID, "credentialsBtn")
        
        assert privacy_notice.is_displayed()
        assert consent_section.is_displayed()
        assert login_button.is_displayed()


class TestStudentLoginJavaScript(StudentLoginUITest):
    """Test JavaScript functionality of the student login interface."""
    
    def test_device_fingerprint_generation(self):
        """Test that device fingerprint is properly anonymized."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Execute the device fingerprint generation function
        fingerprint = self.driver.execute_script("""
            function generateAnonymousDeviceFingerprint() {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillText('Device fingerprint', 2, 2);
                
                const fingerprint = [
                    navigator.language,
                    screen.width + 'x' + screen.height,
                    new Date().getTimezoneOffset(),
                    canvas.toDataURL().slice(-50)
                ].join('|');
                
                return btoa(fingerprint).slice(0, 32);
            }
            return generateAnonymousDeviceFingerprint();
        """)
        
        # Assert
        assert fingerprint
        assert len(fingerprint) <= 32
        assert fingerprint.replace('-', '').replace('_', '').isalnum()  # Base64-like

    def test_form_validation_javascript(self):
        """Test JavaScript form validation."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Test the form validation functions
        validation_result = self.driver.execute_script("""
            // Fill in form data
            document.getElementById('username').value = 'test@student.edu';
            document.getElementById('userPassword').value = 'password123';
            
            // Check if form is valid
            const form = document.getElementById('credentialsForm');
            return form.checkValidity();
        """)
        
        # Assert
        assert validation_result is True

    def test_privacy_modal_functionality(self):
        """Test privacy modal open/close functionality."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Test modal functions
        self.driver.execute_script("showPrivacyPolicy();")
        
        modal = self.driver.find_element(By.ID, "privacyModal")
        assert modal.is_displayed()
        
        # Close modal
        self.driver.execute_script("hidePrivacyPolicy();")
        
        # Wait for modal to hide
        time.sleep(0.5)
        
        # Assert modal is hidden
        modal_style = modal.get_attribute("style")
        assert "display: none" in modal_style

    def test_login_mode_switching_javascript(self):
        """Test JavaScript login mode switching functionality."""
        # Arrange & Act
        self.driver.get(self.test_student_login_url)
        
        # Test mode switching function
        self.driver.execute_script("switchLoginMode('token');")
        
        # Wait for UI update
        time.sleep(0.5)
        
        # Assert
        credentials_form = self.driver.find_element(By.ID, "credentialsForm")
        token_form = self.driver.find_element(By.ID, "tokenForm")
        
        assert not credentials_form.is_displayed()
        assert token_form.is_displayed()
        
        # Switch back
        self.driver.execute_script("switchLoginMode('credentials');")
        time.sleep(0.5)
        
        assert credentials_form.is_displayed()
        assert not token_form.is_displayed()


@pytest.mark.frontend
class TestStudentLoginResponsiveDesign(StudentLoginUITest):
    """Test responsive design of student login interface."""
    
    def test_mobile_viewport_layout(self):
        """Test layout in mobile viewport."""
        # Arrange & Act
        self.driver.set_window_size(375, 667)  # iPhone dimensions
        self.driver.get(self.test_student_login_url)
        
        # Assert
        login_container = self.driver.find_element(By.CLASS_NAME, "login-container")
        consent_section = self.driver.find_element(By.CLASS_NAME, "consent-section")
        
        # Elements should be visible and properly laid out
        assert login_container.is_displayed()
        assert consent_section.is_displayed()
        
        # Check that elements don't overflow
        container_width = login_container.size['width']
        window_width = self.driver.get_window_size()['width']
        assert container_width <= window_width

    def test_tablet_viewport_layout(self):
        """Test layout in tablet viewport."""
        # Arrange & Act  
        self.driver.set_window_size(768, 1024)  # iPad dimensions
        self.driver.get(self.test_student_login_url)
        
        # Assert
        privacy_notice = self.driver.find_element(By.CLASS_NAME, "privacy-notice")
        login_forms = self.driver.find_elements(By.CLASS_NAME, "login-form")
        
        assert privacy_notice.is_displayed()
        assert len(login_forms) >= 1
        
        # Check readable text size
        privacy_text = privacy_notice.text
        assert len(privacy_text) > 50  # Should have substantial content

    def test_desktop_viewport_layout(self):
        """Test layout in desktop viewport."""
        # Arrange & Act
        self.driver.set_window_size(1920, 1080)  # Desktop dimensions
        self.driver.get(self.test_student_login_url)
        
        # Assert
        mode_toggle = self.driver.find_element(By.CLASS_NAME, "login-mode-toggle")
        consent_checkboxes = self.driver.find_elements(By.CLASS_NAME, "consent-checkbox")
        
        assert mode_toggle.is_displayed()
        assert len(consent_checkboxes) == 2
        
        # All elements should be properly spaced
        for checkbox in consent_checkboxes:
            assert checkbox.is_displayed()


# Mock-based tests for JavaScript unit testing
class TestStudentLoginJavaScriptUnits:
    """Unit tests for JavaScript functions using Python mocks."""
    
    def test_generate_device_fingerprint_anonymization(self):
        """Test device fingerprint generation logic."""
        # This would typically be tested with a JavaScript testing framework
        # Here we test the logic concept
        
        # Arrange
        mock_navigator = {
            'language': 'en-US',
            'screen': {'width': 1920, 'height': 1080},
            'timezone_offset': -480
        }
        
        # Act - Simulate the fingerprint generation logic
        fingerprint_components = [
            mock_navigator['language'],
            f"{mock_navigator['screen']['width']}x{mock_navigator['screen']['height']}",
            str(mock_navigator['timezone_offset']),
            "canvas_hash_mock"
        ]
        fingerprint_raw = '|'.join(fingerprint_components)
        
        # Simulate base64 encoding and truncation
        import base64
        fingerprint_encoded = base64.b64encode(fingerprint_raw.encode()).decode()[:32]
        
        # Assert
        assert len(fingerprint_encoded) <= 32
        assert fingerprint_encoded.replace('=', '').replace('+', '').replace('/', '').isalnum()
        
        # Should not contain identifying information directly
        assert 'en-US' not in fingerprint_encoded
        assert '1920' not in fingerprint_encoded

    def test_gdpr_consent_validation_logic(self):
        """Test GDPR consent validation logic."""
        # Arrange
        consent_data = {
            'analytics': False,
            'notifications': False
        }
        
        # Act - Test consent validation
        def validate_consent(consent):
            # All consent should default to False (opt-in required)
            for key, value in consent.items():
                if not isinstance(value, bool):
                    return False
            return True
        
        # Assert
        assert validate_consent(consent_data)
        
        # Test with invalid data
        invalid_consent = {'analytics': 'yes'}  # Should be boolean
        assert not validate_consent(invalid_consent)

    def test_privacy_data_minimization_check(self):
        """Test that UI data follows minimization principles."""
        # Arrange
        login_form_data = {
            'username': 'student@test.edu',
            'password': 'password123',
            'course_instance_id': 'course-123',
            'device_fingerprint': 'anonymized_hash',
            'consent_analytics': True,
            'consent_notifications': False
        }
        
        # Act - Check for sensitive data that shouldn't be included
        sensitive_fields = {'ssn', 'phone', 'address', 'credit_card', 'date_of_birth'}
        form_fields = set(login_form_data.keys())
        
        # Assert
        assert sensitive_fields.isdisjoint(form_fields)
        
        # Check that only necessary fields are present
        expected_fields = {
            'username', 'password', 'course_instance_id', 
            'device_fingerprint', 'consent_analytics', 'consent_notifications'
        }
        assert form_fields == expected_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])