"""
Integration test for the complete registration flow
Tests the fixed JavaScript DOM issue and CORS configuration
"""
import requests
import json
import pytest

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class TestRegistrationFlow:
    """Test the complete user registration flow"""
    
    @pytest.fixture
    def chrome_options(self):
        """Configure Chrome options for testing"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return options
    
    def test_api_registration_works(self):
        """Test that the registration API endpoint works correctly"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        url = "http://localhost:8000/auth/register"
        data = {
            "email": f"testapi{unique_id}@example.com",
            "full_name": "Test API User",
            "username": f"testapi{unique_id}",
            "password": "testpass123"
        }
        
        response = requests.post(url, json=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["email"] == f"testapi{unique_id}@example.com"
        assert result["full_name"] == "Test API User"
        assert result["username"] == f"testapi{unique_id}"
        assert result["is_active"] is True
        assert "id" in result
        
    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured for frontend"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        url = "http://localhost:8000/auth/register"
        headers = {
            "Content-Type": "application/json",
            "Origin": "http://localhost:8080"
        }
        data = {
            "email": f"testcors{unique_id}@example.com",
            "full_name": "Test CORS User",
            "username": f"testcors{unique_id}",
            "password": "testpass123"
        }
        
        response = requests.post(url, json=data, headers=headers)
        assert response.status_code == 200
        
        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:8080"
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"
        
    def test_user_service_health(self):
        """Test that the user management service is healthy"""
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data
        
    @pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
    def test_frontend_registration_flow(self, chrome_options):
        """Test the complete frontend registration flow"""
        # This test would require selenium setup
        # Including it to show what comprehensive testing looks like
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to frontend
            driver.get("http://localhost:8080")
            
            # Click register button
            register_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Register')]"))
            )
            register_button.click()
            
            # Fill registration form
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "register-email"))
            )
            email_field.send_keys("seleniumtest@example.com")
            
            driver.find_element(By.ID, "register-name").send_keys("Selenium Test User")
            driver.find_element(By.ID, "register-username").send_keys("seleniumuser")
            driver.find_element(By.ID, "register-password").send_keys("testpass123")
            driver.find_element(By.ID, "register-password-confirm").send_keys("testpass123")
            
            # Submit form
            submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            
            # Wait for success message or redirect
            WebDriverWait(driver, 10).until(
                lambda d: "successful" in d.page_source.lower() or 
                         "login" in d.current_url.lower()
            )
            
            # Verify no JavaScript errors occurred
            logs = driver.get_log('browser')
            js_errors = [log for log in logs if log['level'] == 'SEVERE']
            assert len(js_errors) == 0, f"JavaScript errors found: {js_errors}"
            
        finally:
            driver.quit()


if __name__ == "__main__":
    # Run basic tests without Selenium
    test = TestRegistrationFlow()
    test.test_api_registration_works()
    test.test_cors_headers_present()
    test.test_user_service_health()
    print("✅ All registration flow tests passed!")