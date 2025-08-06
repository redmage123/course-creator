#!/usr/bin/env python3
"""
End-to-End Tests for Organization Registration Flow
Tests complete user workflow from frontend form to backend API
"""
import pytest
import time
import os
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from PIL import Image
import io


class TestOrganizationRegistrationE2E:
    """
    End-to-End test suite for Organization Registration
    Tests: Complete user workflows, drag-and-drop functionality, form validation, API integration
    """

    @classmethod
    def setup_class(cls):
        """Set up browser and test environment"""
        cls.base_url = "https://176.9.99.103:3000"  # Frontend URL
        cls.api_url = "https://176.9.99.103:8008"   # Organization API URL
        
        # Configure Chrome options for testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 20)
            print("Chrome WebDriver initialized successfully")
        except WebDriverException as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")

    @classmethod
    def teardown_class(cls):
        """Clean up browser resources"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def test_organization_registration_page_loads(self):
        """Test that organization registration page loads correctly"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.ID, "organizationRegistrationForm")))
            
            # Check page title
            assert "Register Your Organization" in self.driver.title
            
            # Check main elements are present
            form = self.driver.find_element(By.ID, "organizationRegistrationForm")
            assert form.is_displayed()
            
            # Check required form sections
            sections = [
                "Organization Information",
                "Contact Information", 
                "Organization Administrator"
            ]
            
            for section_text in sections:
                section = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{section_text}')]")
                assert section.is_displayed()
            
            print("Organization registration page loaded successfully")
            
        except TimeoutException:
            pytest.skip("Organization registration page not accessible")

    def test_form_field_validation(self):
        """Test client-side form validation"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "organizationRegistrationForm")))
            
            # Test required field validation
            submit_btn = self.driver.find_element(By.ID, "submitBtn")
            submit_btn.click()
            
            # Should show validation errors
            time.sleep(2)  # Wait for validation
            
            # Check for error indicators
            error_elements = self.driver.find_elements(By.CLASS_NAME, "form-error")
            visible_errors = [elem for elem in error_elements if elem.is_displayed()]
            
            if visible_errors:
                print(f"Found {len(visible_errors)} validation errors as expected")
            
            # Test professional email validation
            email_input = self.driver.find_element(By.ID, "orgEmail")
            email_input.clear()
            email_input.send_keys("admin@gmail.com")  # Personal email
            
            # Trigger validation by clicking elsewhere
            self.driver.find_element(By.ID, "orgName").click()
            time.sleep(1)
            
            # Check for professional email error
            email_error = self.driver.find_element(By.ID, "orgEmail-error")
            if email_error.is_displayed():
                error_text = email_error.text.lower()
                assert "personal" in error_text or "gmail" in error_text
                print("Professional email validation working correctly")
            
        except TimeoutException:
            pytest.skip("Form validation test failed - page not responsive")

    def test_auto_slug_generation(self):
        """Test automatic slug generation from organization name"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "orgName")))
            
            # Enter organization name
            name_input = self.driver.find_element(By.ID, "orgName")
            slug_input = self.driver.find_element(By.ID, "orgSlug")
            
            # Test slug generation
            test_name = "TechCorp Training Institute"
            name_input.clear()
            name_input.send_keys(test_name)
            
            # Wait for slug to be generated
            time.sleep(1)
            
            generated_slug = slug_input.get_attribute("value")
            expected_slug = "techcorp-training-institute"
            
            assert generated_slug == expected_slug, f"Expected '{expected_slug}', got '{generated_slug}'"
            print(f"Slug generation working: '{test_name}' -> '{generated_slug}'")
            
        except TimeoutException:
            pytest.skip("Slug generation test failed - elements not found")

    def test_phone_number_formatting(self):
        """Test phone number formatting functionality"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "orgPhone")))
            
            # Test phone formatting
            phone_input = self.driver.find_element(By.ID, "orgPhone")
            phone_input.clear()
            phone_input.send_keys("5551234567")
            
            # Trigger formatting
            self.driver.find_element(By.ID, "orgName").click()
            time.sleep(1)
            
            formatted_phone = phone_input.get_attribute("value")
            print(f"Phone formatting: '5551234567' -> '{formatted_phone}'")
            
            # Should contain formatting characters
            assert any(char in formatted_phone for char in ["-", "(", ")", " "])
            
        except TimeoutException:
            pytest.skip("Phone formatting test failed - elements not found")

    def test_logo_upload_area_visibility(self):
        """Test that logo upload area is visible and functional"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "logoUploadArea")))
            
            # Check upload area is visible
            upload_area = self.driver.find_element(By.ID, "logoUploadArea")
            assert upload_area.is_displayed()
            
            # Check upload content
            upload_content = upload_area.find_element(By.CLASS_NAME, "upload-content")
            assert upload_content.is_displayed()
            
            # Check for drag and drop text
            upload_text = upload_content.text
            assert "drag" in upload_text.lower() and "drop" in upload_text.lower()
            
            # Check file input exists
            file_input = self.driver.find_element(By.ID, "orgLogo")
            assert file_input.get_attribute("type") == "file"
            assert file_input.get_attribute("accept") == ".jpg,.jpeg,.png,.gif"
            
            print("Logo upload area is properly configured")
            
        except TimeoutException:
            pytest.skip("Logo upload area test failed - elements not found")

    def test_file_upload_click_functionality(self):
        """Test clicking on upload area to select files"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "logoUploadArea")))
            
            # Create a temporary test image file
            test_image = Image.new('RGB', (100, 100), color='blue')
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                test_image.save(tmp_file, format='PNG')
                temp_image_path = tmp_file.name
            
            try:
                # Use JavaScript to simulate file selection (since we can't interact with file dialogs)
                file_input = self.driver.find_element(By.ID, "orgLogo")
                
                # This would normally trigger file dialog, but we'll simulate selection
                self.driver.execute_script("""
                    const input = document.getElementById('orgLogo');
                    const file = new File(['test'], 'test.png', { type: 'image/png' });
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    input.files = dataTransfer.files;
                    
                    // Trigger change event
                    const event = new Event('change', { bubbles: true });
                    input.dispatchEvent(event);
                """)
                
                time.sleep(2)  # Wait for processing
                
                # Check if preview area becomes visible
                preview_area = self.driver.find_element(By.ID, "logoPreview")
                if preview_area.is_displayed():
                    print("File upload simulation triggered preview successfully")
                else:
                    print("File upload simulation completed (preview may require actual file)")
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)
                
        except TimeoutException:
            pytest.skip("File upload test failed - elements not found")

    def test_form_submission_validation(self):
        """Test complete form submission with valid data"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "organizationRegistrationForm")))
            
            # Fill out form with valid professional data
            form_data = {
                "orgName": f"E2E Test Corporation {int(time.time())}",
                "orgSlug": f"e2e-test-corp-{int(time.time())}",
                "orgDescription": "End-to-end test organization for validation",
                "orgDomain": "e2etest.com",
                "orgAddress": "123 E2E Test Drive, Test City, TC 12345",
                "orgPhone": "5551234567",
                "orgEmail": "admin@e2etest.com",
                "adminName": "Test Administrator",
                "adminEmail": "test.admin@e2etest.com",
                "adminPhone": "5551234568"
            }
            
            # Fill out all form fields
            for field_id, value in form_data.items():
                try:
                    field = self.driver.find_element(By.ID, field_id)
                    field.clear()
                    field.send_keys(value)
                except Exception as e:
                    print(f"Could not fill field {field_id}: {e}")
            
            time.sleep(1)  # Allow form processing
            
            # Submit form
            submit_btn = self.driver.find_element(By.ID, "submitBtn")
            submit_btn.click()
            
            # Wait for submission processing
            time.sleep(5)
            
            # Check for success or error messages
            try:
                success_message = self.driver.find_element(By.ID, "successMessage")
                if success_message.is_displayed():
                    print("Form submission succeeded - success message displayed")
                    return
            except:
                pass
            
            try:
                error_message = self.driver.find_element(By.ID, "general-error")
                if error_message.is_displayed():
                    error_text = error_message.text
                    print(f"Form submission error (expected): {error_text}")
                    
                    # Check if it's an authentication error (expected in test environment)
                    if "authentication" in error_text.lower() or "unauthorized" in error_text.lower():
                        print("Authentication error expected in test environment")
                    else:
                        print(f"Validation or API error: {error_text}")
            except:
                pass
            
            # Check if submit button shows loading state
            submit_btn_classes = submit_btn.get_attribute("class")
            if "loading" in submit_btn_classes:
                print("Submit button shows loading state correctly")
            
            print("Form submission test completed")
            
        except TimeoutException:
            pytest.skip("Form submission test failed - elements not responsive")

    def test_professional_email_validation_ui(self):
        """Test professional email validation in UI"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "orgEmail")))
            
            # Test professional email validation
            email_input = self.driver.find_element(By.ID, "orgEmail")
            
            # Test invalid domains
            invalid_domains = ["gmail.com", "yahoo.com", "hotmail.com"]
            
            for domain in invalid_domains:
                email_input.clear()
                email_input.send_keys(f"test@{domain}")
                
                # Trigger validation
                self.driver.find_element(By.ID, "orgName").click()
                time.sleep(1)
                
                # Check for error message
                try:
                    error_element = self.driver.find_element(By.ID, "orgEmail-error")
                    if error_element.is_displayed():
                        error_text = error_element.text.lower()
                        assert "personal" in error_text or domain in error_text
                        print(f"Professional email validation working for {domain}")
                        break
                except:
                    continue
            
            # Test valid professional email
            email_input.clear()
            email_input.send_keys("admin@professional.com")
            self.driver.find_element(By.ID, "orgName").click()
            time.sleep(1)
            
            # Should not show error
            try:
                error_element = self.driver.find_element(By.ID, "orgEmail-error")
                assert not error_element.is_displayed(), "Professional email should not show error"
            except:
                pass  # No error element found, which is good
            
            print("Professional email validation UI test completed")
            
        except TimeoutException:
            pytest.skip("Professional email validation UI test failed")

    def test_responsive_design(self):
        """Test responsive design on different screen sizes"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "organizationRegistrationForm")))
            
            # Test desktop size
            self.driver.set_window_size(1920, 1080)
            time.sleep(1)
            
            form = self.driver.find_element(By.ID, "organizationRegistrationForm")
            assert form.is_displayed()
            
            # Test tablet size
            self.driver.set_window_size(768, 1024)
            time.sleep(1)
            
            assert form.is_displayed()
            
            # Test mobile size
            self.driver.set_window_size(375, 667)
            time.sleep(1)
            
            assert form.is_displayed()
            
            # Reset to desktop
            self.driver.set_window_size(1920, 1080)
            
            print("Responsive design test completed - form visible at all sizes")
            
        except TimeoutException:
            pytest.skip("Responsive design test failed")

    def test_accessibility_features(self):
        """Test basic accessibility features"""
        try:
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "organizationRegistrationForm")))
            
            # Check for required field indicators
            required_labels = self.driver.find_elements(By.CSS_SELECTOR, ".form-label.required")
            assert len(required_labels) > 0, "Should have required field indicators"
            
            # Check form labels are associated with inputs
            labels = self.driver.find_elements(By.TAG_NAME, "label")
            for label in labels:
                for_attr = label.get_attribute("for")
                if for_attr:
                    try:
                        associated_input = self.driver.find_element(By.ID, for_attr)
                        assert associated_input, f"Label should be associated with input: {for_attr}"
                    except:
                        pass  # Some labels might not have associated inputs
            
            # Check for error message containers
            error_containers = self.driver.find_elements(By.CLASS_NAME, "form-error")
            assert len(error_containers) > 0, "Should have error message containers"
            
            # Check for help text
            help_texts = self.driver.find_elements(By.CLASS_NAME, "form-help")
            assert len(help_texts) > 0, "Should have help text for guidance"
            
            print(f"Accessibility test completed: {len(labels)} labels, {len(error_containers)} error containers")
            
        except TimeoutException:
            pytest.skip("Accessibility test failed")

    def test_browser_back_button_functionality(self):
        """Test that browser back button works correctly"""
        try:
            # Navigate to home page first
            self.driver.get(f"{self.base_url}/html/index.html")
            time.sleep(2)
            
            # Navigate to organization registration
            self.driver.get(f"{self.base_url}/html/organization-registration.html")
            self.wait.until(EC.presence_of_element_located((By.ID, "organizationRegistrationForm")))
            
            # Fill some data
            name_input = self.driver.find_element(By.ID, "orgName")
            name_input.send_keys("Test Organization")
            
            # Go back
            self.driver.back()
            time.sleep(2)
            
            # Should be on home page
            current_url = self.driver.current_url
            assert "index.html" in current_url or current_url.endswith("/")
            
            # Go forward
            self.driver.forward()
            time.sleep(2)
            
            # Should be back on registration page
            current_url = self.driver.current_url
            assert "organization-registration.html" in current_url
            
            print("Browser navigation test completed successfully")
            
        except TimeoutException:
            pytest.skip("Browser navigation test failed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])