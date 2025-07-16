"""
Unit tests for the bbrelin course fix - verifying the real user can see their course.
This tests the complete bug fix where bbrelin instructor can see their Introduction to Python course.
"""
import pytest
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from webdriver_manager.chrome import ChromeDriverManager
import requests

# Add path for imports
sys.path.insert(0, '/home/bbrelin/course-creator/tests')

class TestBbrelinCourseFix:
    """Test suite for the bbrelin course fix."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--silent')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--remote-debugging-port=9223')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--disable-hang-monitor')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-component-update')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-domain-reliability')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-translate')
            chrome_options.add_argument('--metrics-recording-only')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--safebrowsing-disable-auto-update')
            chrome_options.add_argument('--enable-automation')
            chrome_options.add_argument('--password-store=basic')
            chrome_options.add_argument('--use-mock-keychain')
            chrome_options.add_argument('--user-data-dir=/tmp/chrome-test-bbrelin')
            
            # Try to use system chromium first
            try:
                chrome_options.binary_location = '/usr/bin/chromium-browser'
                service = Service(ChromeDriverManager(driver_version="138.0.7204.100").install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"Chromium setup failed: {e}")
                # Fallback to regular Chrome
                try:
                    service = Service(ChromeDriverManager(driver_version="138.0.7204.100").install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e2:
                    print(f"Chrome setup also failed: {e2}")
                    # Final fallback to latest version
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            print(f"Skipping browser tests - no Chrome available: {e}")
            self.driver = None
    
    def teardown_method(self):
        """Clean up after each test."""
        if self.driver:
            self.driver.quit()
    
    def test_bbrelin_can_authenticate(self):
        """Test that bbrelin can authenticate successfully."""
        login_data = {
            "username": "bbrelin@gmail.com",
            "password": "P0stgr3s:atao12e"
        }
        
        login_response = requests.post("http://localhost:8000/auth/login", data=login_data)
        assert login_response.status_code == 200, "Bbrelin should be able to login"
        
        token = login_response.json().get('access_token')
        assert token is not None, "Should receive access token"
        
        print("✅ Bbrelin authentication test passed")
    
    def test_bbrelin_sees_python_course_in_api(self):
        """Test that bbrelin sees the Introduction to Python course via API."""
        # Login to get token
        login_data = {
            "username": "bbrelin@gmail.com",
            "password": "P0stgr3s:atao12e"
        }
        
        login_response = requests.post("http://localhost:8000/auth/login", data=login_data)
        assert login_response.status_code == 200, "Login should succeed"
        
        token = login_response.json().get('access_token')
        assert token is not None, "Should receive access token"
        
        # Test courses API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        courses_response = requests.get("http://localhost:8004/courses", headers=headers)
        assert courses_response.status_code == 200, "Courses API should return 200"
        
        courses_data = courses_response.json()
        assert len(courses_data) == 1, "Bbrelin should have exactly 1 course"
        
        # Verify it's the Python course
        course = courses_data[0]
        assert course['title'] == "Introduction to Python", "Should be the Python course"
        
        print("✅ Bbrelin API test passed: Sees Introduction to Python course")
    
    def test_original_bug_is_fixed(self):
        """Test that the original bug is fixed - bbrelin instructor can see their course."""
        # This test verifies the original issue is resolved:
        # "I still don't see the course I created. the bbrelin instructor has an introduction to python course which isn't showing up"
        
        # Login as bbrelin
        login_data = {
            "username": "bbrelin@gmail.com",
            "password": "P0stgr3s:atao12e"
        }
        
        login_response = requests.post("http://localhost:8000/auth/login", data=login_data)
        assert login_response.status_code == 200, "Bbrelin should be able to authenticate"
        
        token = login_response.json().get('access_token')
        
        # Get courses
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        courses_response = requests.get("http://localhost:8004/courses", headers=headers)
        assert courses_response.status_code == 200, "Should be able to get courses"
        
        courses = courses_response.json()
        
        # The original bug: bbrelin instructor couldn't see their Introduction to Python course
        # The fix: bbrelin instructor can now see their Introduction to Python course
        assert len(courses) > 0, "ORIGINAL BUG FIX: Bbrelin should see at least 1 course (was 0)"
        
        course_titles = [course.get('title', '') for course in courses]
        assert "Introduction to Python" in course_titles, "ORIGINAL BUG FIX: Bbrelin should see Introduction to Python course"
        
        print("🎉 ORIGINAL BUG FIXED: Bbrelin instructor can now see their Introduction to Python course!")
        return True
    
    def test_test_instructor_has_remaining_course(self):
        """Test that test instructor still has the Java course after transferring Python to bbrelin."""
        # Login as test instructor
        login_data = {
            "username": "instructor@courseplatform.com",
            "password": "Instructor123!"
        }
        
        login_response = requests.post("http://localhost:8000/auth/login", data=login_data)
        assert login_response.status_code == 200, "Test instructor should be able to login"
        
        token = login_response.json().get('access_token')
        
        # Get courses
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        courses_response = requests.get("http://localhost:8004/courses", headers=headers)
        assert courses_response.status_code == 200, "Should be able to get courses"
        
        courses = courses_response.json()
        assert len(courses) == 1, "Test instructor should have 1 course (Java Fundamentals)"
        
        course_titles = [course.get('title', '') for course in courses]
        assert "Java Fundamentals" in course_titles, "Test instructor should have Java Fundamentals"
        assert "Introduction to Python" not in course_titles, "Python course should be transferred to bbrelin"
        
        print("✅ Test instructor correctly has Java Fundamentals course only")