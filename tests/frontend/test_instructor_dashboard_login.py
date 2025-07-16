"""
Unit tests to verify that the instructor dashboard loads correctly after login
"""
import pytest
import sys
import os
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

# Add path for imports
sys.path.insert(0, '/home/bbrelin/course-creator/tests')

class TestInstructorDashboardLogin:
    """Unit tests for instructor dashboard login functionality"""
    
    def setup_method(self):
        """Set up test fixtures before each test"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--user-data-dir=/tmp/chrome-test-login')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--silent')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            print(f"Skipping browser tests - no Chrome available: {e}")
            self.driver = None
    
    def teardown_method(self):
        """Clean up after each test"""
        if self.driver:
            self.driver.quit()
    
    def test_authentication_api_works(self):
        """Unit test: Authentication API returns valid token"""
        
        login_data = {
            "username": "bbrelin@gmail.com",
            "password": "f00bar123"
        }
        
        try:
            response = requests.post("http://localhost:8000/auth/login", data=login_data)
            assert response.status_code == 200, f"Login should return 200, got {response.status_code}"
            
            data = response.json()
            assert 'access_token' in data, "Response should contain access_token"
            assert data['access_token'] is not None, "Access token should not be None"
            
            print("✅ Authentication API returns valid token")
            return data['access_token']
            
        except Exception as e:
            pytest.fail(f"Authentication API test failed: {e}")
    
    def test_courses_api_with_token(self):
        """Unit test: Courses API works with valid token"""
        
        # First get a token
        token = self.test_authentication_api_works()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get("http://localhost:8004/courses", headers=headers)
            assert response.status_code == 200, f"Courses API should return 200, got {response.status_code}"
            
            courses = response.json()
            assert isinstance(courses, list), "Courses should be a list"
            assert len(courses) >= 1, "Should have at least 1 course for bbrelin"
            
            # Check course structure
            course = courses[0]
            required_fields = ['id', 'title', 'description', 'instructor_id']
            for field in required_fields:
                assert field in course, f"Course should have {field} field"
            
            print("✅ Courses API works with valid token")
            return courses
            
        except Exception as e:
            pytest.fail(f"Courses API test failed: {e}")
    
    def test_dashboard_html_structure(self):
        """Unit test: Dashboard HTML has required structure"""
        
        dashboard_path = '/home/bbrelin/course-creator/frontend/instructor-dashboard.html'
        
        try:
            with open(dashboard_path, 'r') as f:
                content = f.read()
        except Exception as e:
            pytest.fail(f"Could not read dashboard HTML: {e}")
        
        # Check for essential elements
        required_elements = [
            'dashboard-layout',
            'dashboard-sidebar',
            'dashboard-main',
            'main-content',
            'loadUserCourses',
            'updateCoursesDisplay',
            'localStorage.getItem'
        ]
        
        for element in required_elements:
            assert element in content, f"Dashboard should contain {element}"
        
        print("✅ Dashboard HTML has required structure")
    
    def test_dashboard_loads_without_redirect(self):
        """Unit test: Dashboard loads without automatic redirect"""
        
        if not self.driver:
            pytest.skip("No browser available")
        
        try:
            # Get authentication token
            token = self.test_authentication_api_works()
            
            # Load dashboard with authentication
            dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
            self.driver.get(dashboard_url)
            
            # Inject authentication
            self.driver.execute_script(f"""
                localStorage.setItem('authToken', '{token}');
                localStorage.setItem('currentUser', JSON.stringify({{
                    id: 'cd7f5be1-bac8-49cd-8034-0f7ded517efd',
                    email: 'bbrelin@gmail.com',
                    full_name: 'Braun Brelin',
                    role: 'instructor'
                }}));
            """)
            
            # Reload to apply authentication
            self.driver.refresh()
            
            # Wait for dashboard to load
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-layout")))
            
            print("✅ Dashboard loads with authentication")
            
            # Check that we're not automatically redirected to overview
            time.sleep(2)  # Give time for any automatic redirects
            
            # Check which sections are active
            active_sections = self.driver.find_elements(By.CSS_SELECTOR, ".content-section.active")
            
            # Should have no active sections (no automatic redirect)
            assert len(active_sections) == 0, f"Should have no active sections, found {len(active_sections)}"
            
            print("✅ Dashboard loads without automatic redirect")
            
        except TimeoutException:
            pytest.fail("Dashboard failed to load within timeout")
        except Exception as e:
            pytest.fail(f"Dashboard loading test failed: {e}")
    
    def test_dashboard_navigation_works(self):
        """Unit test: Dashboard navigation works after login"""
        
        if not self.driver:
            pytest.skip("No browser available")
        
        try:
            # Get authentication token
            token = self.test_authentication_api_works()
            
            # Load dashboard
            dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
            self.driver.get(dashboard_url)
            
            # Inject authentication
            self.driver.execute_script(f"""
                localStorage.setItem('authToken', '{token}');
                localStorage.setItem('currentUser', JSON.stringify({{
                    id: 'cd7f5be1-bac8-49cd-8034-0f7ded517efd',
                    email: 'bbrelin@gmail.com',
                    full_name: 'Braun Brelin',
                    role: 'instructor'
                }}));
            """)
            
            # Reload to apply authentication
            self.driver.refresh()
            
            # Wait for dashboard to load
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-layout")))
            
            # Test navigation to Overview
            overview_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-section='overview']")))
            overview_link.click()
            
            # Check that overview section is now active
            time.sleep(1)
            overview_section = self.driver.find_element(By.ID, "overview-section")
            assert "active" in overview_section.get_attribute("class"), "Overview section should be active after clicking"
            
            print("✅ Navigation to Overview works")
            
            # Test navigation to My Courses
            courses_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-section='courses']")))
            courses_link.click()
            
            # Check that courses section is now active
            time.sleep(1)
            courses_section = self.driver.find_element(By.ID, "courses-section")
            assert "active" in courses_section.get_attribute("class"), "Courses section should be active after clicking"
            
            print("✅ Navigation to My Courses works")
            
        except Exception as e:
            pytest.fail(f"Dashboard navigation test failed: {e}")
    
    def test_courses_display_after_login(self):
        """Unit test: Courses display correctly after login"""
        
        if not self.driver:
            pytest.skip("No browser available")
        
        try:
            # Get authentication token
            token = self.test_authentication_api_works()
            
            # Load dashboard
            dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
            self.driver.get(dashboard_url)
            
            # Inject authentication
            self.driver.execute_script(f"""
                localStorage.setItem('authToken', '{token}');
                localStorage.setItem('currentUser', JSON.stringify({{
                    id: 'cd7f5be1-bac8-49cd-8034-0f7ded517efd',
                    email: 'bbrelin@gmail.com',
                    full_name: 'Braun Brelin',
                    role: 'instructor'
                }}));
            """)
            
            # Reload to apply authentication
            self.driver.refresh()
            
            # Wait for dashboard to load
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-layout")))
            
            # Wait for courses to load
            time.sleep(3)
            
            # Navigate to courses section
            courses_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-section='courses']")))
            courses_link.click()
            
            # Wait for courses section to be active
            time.sleep(2)
            
            # Check that courses are displayed
            courses_list = self.driver.find_element(By.ID, "courses-list")
            assert courses_list is not None, "Courses list element should exist"
            
            # Check for course cards
            course_cards = self.driver.find_elements(By.CLASS_NAME, "course-card")
            assert len(course_cards) >= 1, f"Should have at least 1 course card, found {len(course_cards)}"
            
            # Check course card content
            first_card = course_cards[0]
            card_text = first_card.text
            assert "Introduction to Python" in card_text, "Should show Introduction to Python course"
            
            print("✅ Courses display correctly after login")
            
        except Exception as e:
            pytest.fail(f"Courses display test failed: {e}")
    
    def test_complete_login_to_dashboard_flow(self):
        """Integration test: Complete flow from login to dashboard"""
        
        if not self.driver:
            pytest.skip("No browser available")
        
        try:
            # Step 1: Verify authentication works
            token = self.test_authentication_api_works()
            
            # Step 2: Verify courses API works
            courses = self.test_courses_api_with_token()
            
            # Step 3: Load dashboard
            dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
            self.driver.get(dashboard_url)
            
            # Step 4: Inject authentication (simulating login)
            self.driver.execute_script(f"""
                localStorage.setItem('authToken', '{token}');
                localStorage.setItem('currentUser', JSON.stringify({{
                    id: 'cd7f5be1-bac8-49cd-8034-0f7ded517efd',
                    email: 'bbrelin@gmail.com',
                    full_name: 'Braun Brelin',
                    role: 'instructor'
                }}));
            """)
            
            # Step 5: Reload to apply authentication
            self.driver.refresh()
            
            # Step 6: Wait for dashboard to load
            wait = WebDriverWait(self.driver, 15)
            dashboard_layout = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-layout")))
            assert dashboard_layout is not None, "Dashboard layout should be present"
            
            # Step 7: Check that JavaScript functions are loaded
            functions_loaded = self.driver.execute_script("""
                return typeof window.loadUserCourses === 'function' &&
                       typeof window.updateCoursesDisplay === 'function' &&
                       typeof window.viewCourseDetails === 'function' &&
                       typeof window.showSection === 'function';
            """)
            assert functions_loaded, "All required JavaScript functions should be loaded"
            
            # Step 8: Check that no automatic redirect happened
            time.sleep(2)
            active_sections = self.driver.find_elements(By.CSS_SELECTOR, ".content-section.active")
            assert len(active_sections) == 0, "Should not automatically redirect to any section"
            
            # Step 9: Check that courses were loaded
            user_courses = self.driver.execute_script("return window.userCourses ? window.userCourses.length : 0;")
            assert user_courses >= 1, f"Should have loaded at least 1 course, got {user_courses}"
            
            # Step 10: Test manual navigation works
            courses_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-section='courses']")))
            courses_link.click()
            
            time.sleep(2)
            courses_section = self.driver.find_element(By.ID, "courses-section")
            assert "active" in courses_section.get_attribute("class"), "Manual navigation should work"
            
            print("✅ Complete login to dashboard flow works")
            
        except Exception as e:
            pytest.fail(f"Complete login flow test failed: {e}")
    
    def test_dashboard_loads_without_javascript_errors(self):
        """Unit test: Dashboard loads without JavaScript errors"""
        
        if not self.driver:
            pytest.skip("No browser available")
        
        try:
            # Get authentication token
            token = self.test_authentication_api_works()
            
            # Load dashboard
            dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
            self.driver.get(dashboard_url)
            
            # Inject authentication
            self.driver.execute_script(f"""
                localStorage.setItem('authToken', '{token}');
                localStorage.setItem('currentUser', JSON.stringify({{
                    id: 'cd7f5be1-bac8-49cd-8034-0f7ded517efd',
                    email: 'bbrelin@gmail.com',
                    full_name: 'Braun Brelin',
                    role: 'instructor'
                }}));
            """)
            
            # Reload to apply authentication
            self.driver.refresh()
            
            # Wait for dashboard to load
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-layout")))
            
            # Wait for JavaScript to execute
            time.sleep(3)
            
            # Check for JavaScript errors
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log['level'] == 'SEVERE']
            
            # Filter out expected errors (like network errors for missing resources)
            critical_errors = [error for error in errors if 'is not defined' in error['message']]
            
            assert len(critical_errors) == 0, f"Should have no critical JavaScript errors, found: {[e['message'] for e in critical_errors]}"
            
            print("✅ Dashboard loads without critical JavaScript errors")
            
        except Exception as e:
            pytest.fail(f"JavaScript error test failed: {e}")