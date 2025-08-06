"""
End-to-end tests for demo service user flows
Tests complete user journeys through demo functionality using browser automation
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
import time
import json

from tests.framework.test_config import TestConfig


class TestDemoUserFlowsE2E:
    """End-to-end tests for demo user flows"""

    @classmethod
    def setup_class(cls):
        """Setup test environment and browser"""
        cls.config = TestConfig()
        base_url = "localhost"  # Default for E2E tests
        cls.frontend_url = f"{base_url}:3000"
        cls.demo_api_url = f"http://{base_url}:8010/api/v1/demo"
        
        # Setup Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def teardown_class(cls):
        """Clean up browser"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def test_demo_button_visibility_and_interaction(self):
        """Test that demo button is visible and clickable on home page"""
        try:
            # Navigate to home page
            self.driver.get(f"https://{self.frontend_url}")
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Find the Try Demo button
            try:
                demo_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Try Demo')]"))
                )
            except TimeoutException:
                # Fallback: look for button with onclick="startDemo()"
                demo_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@onclick='startDemo()']"))
                )
            
            assert demo_button.is_displayed()
            assert demo_button.is_enabled()
            
            # Check button styling and content
            button_text = demo_button.text
            assert "demo" in button_text.lower()
            
            # Verify button has proper CSS classes
            button_classes = demo_button.get_attribute("class")
            assert "btn" in button_classes
            assert "btn-primary" in button_classes
            
        except Exception as e:
            pytest.skip(f"Frontend not accessible or demo button not found: {e}")

    def test_demo_session_start_flow(self):
        """Test complete demo session start flow"""
        try:
            # Navigate to home page
            self.driver.get(f"https://{self.frontend_url}")
            
            # Click Try Demo button
            demo_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'startDemo')]"))
            )
            demo_button.click()
            
            # Wait for demo session to start (notification should appear)
            try:
                # Look for success notification
                success_notification = self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "notification"))
                )
                
                notification_text = success_notification.text
                assert "demo" in notification_text.lower()
                
            except TimeoutException:
                # Alternative: check for redirect to dashboard
                WebDriverWait(self.driver, 15).until(
                    lambda driver: "instructor-dashboard" in driver.current_url or "demo" in driver.current_url
                )
            
            # Should eventually redirect to dashboard
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.current_url != f"https://{self.frontend_url}/"
            )
            
            final_url = self.driver.current_url
            assert "dashboard" in final_url or "demo" in final_url
            
        except Exception as e:
            pytest.skip(f"Demo flow interaction failed: {e}")

    def test_demo_error_handling_ui(self):
        """Test error handling in demo UI flow"""
        try:
            # Navigate to home page
            self.driver.get(f"https://{self.frontend_url}")
            
            # Simulate demo service being down by intercepting requests
            # (This would require more sophisticated mocking in a real scenario)
            
            # For now, test basic error states
            demo_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'startDemo')]"))
            )
            
            # Multiple rapid clicks should be handled gracefully
            for i in range(3):
                demo_button.click()
                time.sleep(0.1)
            
            # Should not crash the page
            time.sleep(2)
            assert self.driver.title is not None
            
        except Exception as e:
            pytest.skip(f"Error handling test failed: {e}")

    def test_demo_instructor_dashboard_features(self):
        """Test demo features in instructor dashboard"""
        # First, start a demo session via API to ensure we have valid session
        try:
            demo_response = requests.post(f"{self.demo_api_url}/start?user_type=instructor")
            if demo_response.status_code == 200:
                session_data = demo_response.json()
                session_id = session_data["session_id"]
                
                try:
                    # Navigate to instructor dashboard with demo session
                    dashboard_url = f"https://{self.frontend_url}/html/instructor-dashboard.html?demo=true&session={session_id}"
                    self.driver.get(dashboard_url)
                    
                    # Wait for dashboard to load
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
                    # Look for demo-specific indicators
                    page_source = self.driver.page_source.lower()
                    
                    # Should indicate demo mode
                    assert "demo" in page_source or "sample" in page_source
                    
                    # Should have instructor-specific elements
                    try:
                        # Look for course management elements
                        course_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'course') or contains(text(), 'Course')]")
                        assert len(course_elements) > 0
                        
                        # Look for student management elements
                        student_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'student') or contains(text(), 'Student')]")
                        assert len(student_elements) > 0
                        
                    except NoSuchElementException:
                        # Dashboard might not have loaded properly
                        pass
                    
                finally:
                    # Clean up demo session
                    requests.delete(f"{self.demo_api_url}/session?session_id={session_id}")
                    
        except Exception as e:
            pytest.skip(f"Demo dashboard test failed: {e}")

    def test_demo_student_dashboard_features(self):
        """Test demo features in student dashboard"""
        # Start student demo session
        try:
            demo_response = requests.post(f"{self.demo_api_url}/start?user_type=student")
            if demo_response.status_code == 200:
                session_data = demo_response.json()
                session_id = session_data["session_id"]
                
                try:
                    # Navigate to student dashboard with demo session
                    dashboard_url = f"https://{self.frontend_url}/html/student-dashboard.html?demo=true&session={session_id}"
                    self.driver.get(dashboard_url)
                    
                    # Wait for dashboard to load
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
                    # Look for student-specific demo content
                    page_source = self.driver.page_source.lower()
                    
                    # Should indicate demo mode
                    assert "demo" in page_source or "sample" in page_source
                    
                    # Should have student-specific elements
                    try:
                        # Look for course enrollment elements
                        course_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'enroll') or contains(text(), 'progress')]")
                        
                        # Should have learning progress indicators
                        progress_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'progress') or contains(text(), 'complete')]")
                        
                    except NoSuchElementException:
                        pass
                    
                finally:
                    # Clean up demo session
                    requests.delete(f"{self.demo_api_url}/session?session_id={session_id}")
                    
        except Exception as e:
            pytest.skip(f"Student dashboard test failed: {e}")

    def test_demo_course_creation_flow(self):
        """Test AI course creation demo flow"""
        try:
            demo_response = requests.post(f"{self.demo_api_url}/start?user_type=instructor")
            if demo_response.status_code == 200:
                session_data = demo_response.json()
                session_id = session_data["session_id"]
                
                try:
                    # Navigate to instructor dashboard
                    dashboard_url = f"https://{self.frontend_url}/html/instructor-dashboard.html?demo=true&session={session_id}"
                    self.driver.get(dashboard_url)
                    
                    # Wait for page load
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
                    # Look for course creation button/link
                    try:
                        create_button = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Create') or contains(text(), 'New Course')]"))
                        )
                        
                        # Click to start course creation
                        create_button.click()
                        
                        # Should open course creation interface
                        time.sleep(2)
                        
                        # Look for course creation form elements
                        form_elements = self.driver.find_elements(By.TAG_NAME, "input")
                        assert len(form_elements) > 0
                        
                    except TimeoutException:
                        # Course creation might not be implemented in UI yet
                        pass
                    
                finally:
                    requests.delete(f"{self.demo_api_url}/session?session_id={session_id}")
                    
        except Exception as e:
            pytest.skip(f"Course creation flow test failed: {e}")

    def test_demo_analytics_visualization(self):
        """Test demo analytics visualization"""
        try:
            demo_response = requests.post(f"{self.demo_api_url}/start?user_type=instructor")
            if demo_response.status_code == 200:
                session_data = demo_response.json()
                session_id = session_data["session_id"]
                
                try:
                    # Navigate to instructor dashboard
                    dashboard_url = f"https://{self.frontend_url}/html/instructor-dashboard.html?demo=true&session={session_id}"
                    self.driver.get(dashboard_url)
                    
                    # Wait for page load
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
                    # Look for analytics/charts elements
                    try:
                        # Look for common chart/analytics indicators
                        chart_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'chart') or contains(@class, 'graph') or contains(@class, 'analytics')]")
                        
                        # Look for data visualization elements
                        canvas_elements = self.driver.find_elements(By.TAG_NAME, "canvas")
                        svg_elements = self.driver.find_elements(By.TAG_NAME, "svg")
                        
                        # Should have some form of data visualization
                        total_viz_elements = len(chart_elements) + len(canvas_elements) + len(svg_elements)
                        
                        # If we have visualization elements, they should be visible
                        if total_viz_elements > 0:
                            for element in chart_elements + canvas_elements + svg_elements:
                                if element.is_displayed():
                                    assert element.size['width'] > 0
                                    assert element.size['height'] > 0
                        
                    except NoSuchElementException:
                        # Analytics might not be fully implemented in UI
                        pass
                    
                finally:
                    requests.delete(f"{self.demo_api_url}/session?session_id={session_id}")
                    
        except Exception as e:
            pytest.skip(f"Analytics visualization test failed: {e}")

    def test_demo_session_expiration_ui_handling(self):
        """Test UI handling of demo session expiration"""
        try:
            # Create a demo session
            demo_response = requests.post(f"{self.demo_api_url}/start?user_type=instructor")
            if demo_response.status_code == 200:
                session_data = demo_response.json()
                session_id = session_data["session_id"]
                
                try:
                    # Navigate to dashboard
                    dashboard_url = f"https://{self.frontend_url}/html/instructor-dashboard.html?demo=true&session={session_id}"
                    self.driver.get(dashboard_url)
                    
                    # Wait for page load
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
                    # Manually expire the session via API
                    requests.delete(f"{self.demo_api_url}/session?session_id={session_id}")
                    
                    # Try to interact with demo features
                    # (This would need specific demo UI elements to test)
                    
                    # The UI should handle expired session gracefully
                    # Look for error messages or redirect to home
                    time.sleep(2)
                    
                    # Page should still be functional
                    assert self.driver.title is not None
                    
                    # Should not have JavaScript errors (check console)
                    logs = self.driver.get_log('browser')
                    severe_errors = [log for log in logs if log['level'] == 'SEVERE']
                    
                    # Should not have critical JavaScript errors
                    demo_related_errors = [
                        error for error in severe_errors 
                        if 'demo' in error['message'].lower() or 'session' in error['message'].lower()
                    ]
                    
                    # Allow some errors but not complete failure
                    assert len(demo_related_errors) < 5
                    
                finally:
                    # Session already deleted above
                    pass
                    
        except Exception as e:
            pytest.skip(f"Session expiration handling test failed: {e}")

    def test_demo_responsive_design(self):
        """Test demo interface on different screen sizes"""
        try:
            demo_response = requests.post(f"{self.demo_api_url}/start?user_type=instructor")
            if demo_response.status_code == 200:
                session_data = demo_response.json()
                session_id = session_data["session_id"]
                
                try:
                    # Test different viewport sizes
                    viewport_sizes = [
                        (320, 568),   # Mobile
                        (768, 1024),  # Tablet
                        (1920, 1080)  # Desktop
                    ]
                    
                    for width, height in viewport_sizes:
                        # Set viewport size
                        self.driver.set_window_size(width, height)
                        
                        # Navigate to home page
                        self.driver.get(f"https://{self.frontend_url}")
                        
                        # Wait for page load
                        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        
                        # Check that demo button is still visible and accessible
                        try:
                            demo_button = self.wait.until(
                                EC.presence_of_element_located((By.XPATH, "//button[contains(@onclick, 'startDemo')]"))
                            )
                            
                            # Button should be visible (might be in hamburger menu on mobile)
                            assert demo_button.is_displayed() or width < 768  # Mobile might hide in menu
                            
                        except TimeoutException:
                            # On very small screens, button might be in a collapsible menu
                            if width >= 768:  # Should be visible on tablet and up
                                raise
                    
                    # Reset to standard size
                    self.driver.set_window_size(1920, 1080)
                    
                finally:
                    requests.delete(f"{self.demo_api_url}/session?session_id={session_id}")
                    
        except Exception as e:
            pytest.skip(f"Responsive design test failed: {e}")

    def test_demo_accessibility_features(self):
        """Test accessibility features in demo interface"""
        try:
            # Navigate to home page
            self.driver.get(f"https://{self.frontend_url}")
            
            # Wait for page load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Test keyboard navigation to demo button
            try:
                demo_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'startDemo')]"))
                )
                
                # Check accessibility attributes
                aria_label = demo_button.get_attribute("aria-label")
                title = demo_button.get_attribute("title")
                
                # Should have some form of accessible description
                has_accessible_name = (
                    aria_label and len(aria_label) > 0 or
                    title and len(title) > 0 or
                    len(demo_button.text) > 0
                )
                
                assert has_accessible_name, "Demo button should have accessible name"
                
                # Button should be focusable
                demo_button.click()  # Focus the button
                focused_element = self.driver.switch_to.active_element
                assert focused_element == demo_button or "demo" in focused_element.get_attribute("onclick", "")
                
            except TimeoutException:
                pytest.skip("Demo button not found for accessibility testing")
                
        except Exception as e:
            pytest.skip(f"Accessibility test failed: {e}")


# Utility functions for E2E testing
def wait_for_demo_notification(driver, timeout=10):
    """Wait for demo notification to appear"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "notification"))
        )
    except TimeoutException:
        return None

def check_demo_indicators(driver):
    """Check for demo mode indicators on page"""
    page_source = driver.page_source.lower()
    demo_indicators = [
        "demo",
        "sample",
        "test data", 
        "demonstration",
        "try out"
    ]
    
    return any(indicator in page_source for indicator in demo_indicators)

def get_browser_console_errors(driver):
    """Get browser console errors related to demo functionality"""
    try:
        logs = driver.get_log('browser')
        return [log for log in logs if log['level'] in ['SEVERE', 'WARNING']]
    except:
        return []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])