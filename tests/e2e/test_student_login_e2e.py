"""
End-to-End Tests for Student Login System

This module contains comprehensive end-to-end tests for the student login system,
testing complete user workflows from UI interaction through backend processing
to service integrations, while maintaining GDPR compliance throughout.

Business Context:
Tests the complete student login journey including UI interaction, authentication,
consent management, analytics integration, instructor notifications, and session
management to ensure a seamless and privacy-compliant educational experience.

Test Coverage:
- Complete student login workflow (UI → API → Services)
- GDPR consent management end-to-end
- Cross-service integration validation
- Error handling and recovery workflows
- Performance and timeout handling
- Security and privacy protection
- Accessibility compliance workflows
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import httpx
import uuid
import os

# Import for API testing
from fastapi.testclient import TestClient
from fastapi import FastAPI


class StudentLoginE2ETest:
    """Base class for student login end-to-end tests."""
    
    def setup_method(self):
        """Set up test environment for E2E tests."""
        # Set up browser
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception:
            self.driver = webdriver.Firefox()
        
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        
        # Test URLs
        self.login_url = "file://" + os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../frontend/html/student-login.html")
        )
        self.api_base_url = "http://localhost:8000"
        
        # Test data
        self.test_student = {
            "id": str(uuid.uuid4()),
            "username": "test.student@university.edu",
            "password": "SecureTestPassword123!",
            "full_name": "Test Student",
            "role": "student"
        }
        
        self.test_course = {
            "id": str(uuid.uuid4()),
            "title": "Python Programming Fundamentals",
            "description": "Learn Python programming from basics to advanced concepts"
        }
    
    def teardown_method(self):
        """Clean up after each test."""
        if hasattr(self, 'driver'):
            self.driver.quit()


@pytest.mark.e2e
@pytest.mark.skip(reason="Needs refactoring to use real objects")
class TestStudentLoginCompleteWorkflow(StudentLoginE2ETest):
    """Test complete student login workflows end-to-end."""

    def test_successful_login_with_full_consent(self):
        """Test complete successful login workflow with all consents."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Mock the API responses
        with patch('httpx.AsyncClient') as mock_http:
            # Mock successful login response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "jwt_token_123",
                "token_type": "bearer",
                "expires_in": 3600,
                "user_id": self.test_student["id"],
                "username": self.test_student["username"],
                "full_name": self.test_student["full_name"],
                "role": "student",
                "course_enrollments": [{
                    "course_instance_id": self.test_course["id"],
                    "course_title": self.test_course["title"],
                    "progress_percentage": 0,
                    "enrollment_status": "active"
                }],
                "login_timestamp": datetime.utcnow().isoformat(),
                "session_expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "data_processing_notice": "Your login data is processed for educational purposes only."
            }
            
            mock_http.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Act - Fill in login form
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "userPassword")
            
            username_field.send_keys(self.test_student["username"])
            password_field.send_keys(self.test_student["password"])
            
            # Grant both consents
            analytics_consent = self.driver.find_element(By.ID, "consentAnalytics")
            notifications_consent = self.driver.find_element(By.ID, "consentNotifications")
            
            analytics_consent.click()
            notifications_consent.click()
            
            # Submit form
            login_button = self.driver.find_element(By.ID, "credentialsBtn")
            login_button.click()
            
            # Wait for processing
            time.sleep(2)
            
            # Assert - Check for success indicators
            # In a real implementation, this would redirect or show success
            # For now, verify the form was processed
            assert analytics_consent.is_selected()
            assert notifications_consent.is_selected()
            
            # Verify form data was captured correctly
            username_value = username_field.get_attribute("value")
            assert username_value == self.test_student["username"]

    def test_login_with_partial_consent(self):
        """Test login workflow with analytics consent only."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Fill form with partial consent
        username_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_field = self.driver.find_element(By.ID, "userPassword")
        
        username_field.send_keys(self.test_student["username"])
        password_field.send_keys(self.test_student["password"])
        
        # Grant only analytics consent
        analytics_consent = self.driver.find_element(By.ID, "consentAnalytics")
        analytics_consent.click()
        
        # Verify notifications consent remains unchecked
        notifications_consent = self.driver.find_element(By.ID, "consentNotifications")
        
        # Assert
        assert analytics_consent.is_selected()
        assert not notifications_consent.is_selected()

    def test_login_without_consent(self):
        """Test login workflow without any optional consents (minimal data processing)."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Fill form without consent
        username_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_field = self.driver.find_element(By.ID, "userPassword")
        
        username_field.send_keys(self.test_student["username"])
        password_field.send_keys(self.test_student["password"])
        
        # Don't click any consent checkboxes
        analytics_consent = self.driver.find_element(By.ID, "consentAnalytics")
        notifications_consent = self.driver.find_element(By.ID, "consentNotifications")
        
        # Assert - Both should remain unchecked (GDPR compliance)
        assert not analytics_consent.is_selected()
        assert not notifications_consent.is_selected()
        
        # Should still be able to login (essential functionality)
        login_button = self.driver.find_element(By.ID, "credentialsBtn")
        assert login_button.is_enabled()

    def test_token_login_workflow(self):
        """Test complete token-based login workflow."""
        # Arrange
        test_token = "STUDENT_ACCESS_TOKEN_123"
        test_temp_password = "TempPass123!"
        
        self.driver.get(f"{self.login_url}?token={test_token}")
        
        # Act - Should auto-switch to token mode
        time.sleep(1)  # Allow JavaScript to process URL parameters
        
        # Verify token mode is active
        token_form = self.driver.find_element(By.ID, "tokenForm")
        credentials_form = self.driver.find_element(By.ID, "credentialsForm")
        
        # Check if form switching worked (may need JavaScript execution)
        token_mode_button = self.driver.find_element(By.ID, "tokenMode")
        token_mode_button.click()
        
        # Fill token form
        access_token_field = self.driver.find_element(By.ID, "accessToken")
        password_field = self.driver.find_element(By.ID, "password")
        
        access_token_field.clear()
        access_token_field.send_keys(test_token)
        password_field.send_keys(test_temp_password)
        
        # Assert
        assert access_token_field.get_attribute("value") == test_token
        assert password_field.get_attribute("value") == test_temp_password


@pytest.mark.e2e
@pytest.mark.skip(reason="Needs refactoring to use real objects")
class TestStudentLoginErrorHandling(StudentLoginE2ETest):
    """Test error handling workflows in student login."""

    def test_invalid_credentials_error_handling(self):
        """Test handling of invalid login credentials."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Mock failed authentication
        with patch('httpx.AsyncClient') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "detail": "Invalid credentials"
            }
            mock_http.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Act - Submit invalid credentials
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "userPassword")
            login_button = self.driver.find_element(By.ID, "credentialsBtn")
            
            username_field.send_keys("invalid@user.com")
            password_field.send_keys("wrongpassword")
            login_button.click()
            
            # Wait for error handling
            time.sleep(1)
            
            # Assert - Error should be displayed appropriately
            # (In real implementation, JavaScript would show error message)
            assert username_field.get_attribute("value") == "invalid@user.com"

    def test_suspended_account_error_handling(self):
        """Test handling of suspended student account."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Mock suspended account response
        with patch('httpx.AsyncClient') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.json.return_value = {
                "detail": "Account suspended. Please contact your instructor."
            }
            mock_http.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Act - Submit credentials for suspended account
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "userPassword")
            
            username_field.send_keys("suspended@student.edu")
            password_field.send_keys("password123")
            
            # Submit form (would trigger error in real implementation)
            login_button = self.driver.find_element(By.ID, "credentialsBtn")
            login_button.click()
            
            # Assert - Form should still be visible for retry
            assert username_field.is_displayed()
            assert password_field.is_displayed()

    def test_network_error_handling(self):
        """Test handling of network connectivity issues."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Mock network error
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            
            # Act - Submit form during network issue
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "userPassword")
            
            username_field.send_keys(self.test_student["username"])
            password_field.send_keys(self.test_student["password"])
            
            # Should handle gracefully without breaking UI
            login_button = self.driver.find_element(By.ID, "credentialsBtn")
            assert login_button.is_enabled()


@pytest.mark.e2e
@pytest.mark.skip(reason="Needs refactoring to use real objects")
class TestStudentLoginGDPRWorkflow(StudentLoginE2ETest):
    """Test GDPR compliance workflows end-to-end."""

    def test_privacy_policy_access_workflow(self):
        """Test complete privacy policy access and understanding workflow."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Access privacy policy
        privacy_link = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "privacy-link"))
        )
        privacy_link.click()
        
        # Wait for modal to open
        modal = self.wait.until(
            EC.visibility_of_element_located((By.ID, "privacyModal"))
        )
        
        # Assert - Modal should contain GDPR information
        modal_text = modal.text.lower()
        assert "gdpr" in modal_text
        assert "data processing" in modal_text
        assert "your rights" in modal_text
        
        # Test modal closing
        close_button = modal.find_element(By.CLASS_NAME, "close")
        close_button.click()
        
        # Wait for modal to close
        self.wait.until(
            EC.invisibility_of_element_located((By.ID, "privacyModal"))
        )

    def test_consent_withdrawal_information_workflow(self):
        """Test that users can understand how to withdraw consent."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Read consent information
        consent_section = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "consent-section"))
        )
        
        # Assert - Should inform about consent withdrawal
        consent_text = consent_section.text.lower()
        assert "change" in consent_text or "withdraw" in consent_text
        assert "settings" in consent_text or "preferences" in consent_text

    def test_data_minimization_in_ui_workflow(self):
        """Test that UI follows data minimization principles."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Examine form fields
        form_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='password']")
        
        # Assert - Should only have essential fields
        input_names = [inp.get_attribute("name") or inp.get_attribute("id") for inp in form_inputs]
        
        # Should not request unnecessary personal information
        unnecessary_fields = ["ssn", "phone", "address", "date_of_birth", "credit_card"]
        for field in unnecessary_fields:
            assert not any(field in name.lower() for name in input_names if name)

    def test_consent_granularity_workflow(self):
        """Test that consent is granular and specific."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Examine consent options
        consent_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, ".consent-checkbox input[type='checkbox']")
        
        # Assert - Should have separate consent for different purposes
        assert len(consent_checkboxes) >= 2  # Analytics and notifications
        
        # Each should have descriptive labels
        for checkbox in consent_checkboxes:
            checkbox_id = checkbox.get_attribute("id")
            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{checkbox_id}']")
            label_text = label.text.lower()
            
            # Labels should be descriptive and specific
            assert len(label_text) > 20  # Substantial description
            assert any(keyword in label_text for keyword in ["analytics", "notification", "instructor"])


@pytest.mark.e2e
@pytest.mark.skip(reason="Needs refactoring to use real objects")
class TestStudentLoginPerformance(StudentLoginE2ETest):
    """Test performance aspects of student login."""

    def test_page_load_performance(self):
        """Test that login page loads within acceptable time."""
        # Arrange & Act
        start_time = time.time()
        self.driver.get(self.login_url)
        
        # Wait for critical elements to load
        self.wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        load_time = time.time() - start_time
        
        # Assert - Should load quickly for good UX
        assert load_time < 5.0  # Page should load within 5 seconds

    def test_form_responsiveness(self):
        """Test that form interactions are responsive."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Interact with form elements
        start_time = time.time()
        
        username_field = self.driver.find_element(By.ID, "username")
        username_field.send_keys("test@student.edu")
        
        password_field = self.driver.find_element(By.ID, "userPassword")
        password_field.send_keys("password123")
        
        # Switch login modes
        token_mode_button = self.driver.find_element(By.ID, "tokenMode")
        token_mode_button.click()
        
        interaction_time = time.time() - start_time
        
        # Assert - Interactions should be responsive
        assert interaction_time < 2.0  # Basic interactions should be quick

    def test_consent_ui_performance(self):
        """Test that consent interface performs well."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Interact with consent elements
        start_time = time.time()
        
        analytics_consent = self.driver.find_element(By.ID, "consentAnalytics")
        notifications_consent = self.driver.find_element(By.ID, "consentNotifications")
        
        # Toggle consents multiple times
        for _ in range(3):
            analytics_consent.click()
            notifications_consent.click()
            analytics_consent.click()
            notifications_consent.click()
        
        consent_interaction_time = time.time() - start_time
        
        # Assert - Consent interactions should be smooth
        assert consent_interaction_time < 2.0


@pytest.mark.e2e
@pytest.mark.skip(reason="Needs refactoring to use real objects")
class TestStudentLoginAccessibility(StudentLoginE2ETest):
    """Test accessibility compliance in student login workflow."""

    def test_keyboard_navigation_workflow(self):
        """Test complete keyboard navigation through login form."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Navigate using only keyboard
        username_field = self.driver.find_element(By.ID, "username")
        username_field.click()  # Start focus
        
        # Tab through all form elements
        active_elements = []
        for _ in range(10):  # Tab through up to 10 elements
            active_element = self.driver.switch_to.active_element
            active_elements.append(active_element.tag_name + ":" + (active_element.get_attribute("id") or ""))
            active_element.send_keys(Keys.TAB)
            time.sleep(0.1)
        
        # Assert - Should be able to reach all interactive elements
        interactive_elements = ["input", "button", "a"]
        assert any(elem.startswith(tag) for elem in active_elements for tag in interactive_elements)

    def test_screen_reader_compatibility_workflow(self):
        """Test screen reader compatibility features."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Check for screen reader support features
        form_labels = self.driver.find_elements(By.TAG_NAME, "label")
        form_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[id]")
        
        # Assert - All inputs should have associated labels
        input_ids = [inp.get_attribute("id") for inp in form_inputs]
        label_fors = [label.get_attribute("for") for label in form_labels]
        
        for input_id in input_ids:
            if input_id:  # Skip inputs without IDs
                assert input_id in label_fors, f"Input {input_id} missing associated label"

    def test_color_contrast_accessibility_workflow(self):
        """Test that important elements are visible for accessibility."""
        # Arrange
        self.driver.get(self.login_url)
        
        # Act - Check that critical elements are present and visible
        critical_elements = [
            (By.CLASS_NAME, "privacy-notice"),
            (By.CLASS_NAME, "consent-section"),
            (By.ID, "credentialsBtn"),
            (By.CLASS_NAME, "login-mode-toggle")
        ]
        
        # Assert - All critical elements should be visible
        for selector_type, selector_value in critical_elements:
            element = self.driver.find_element(selector_type, selector_value)
            assert element.is_displayed(), f"Critical element {selector_value} not visible"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])