#!/usr/bin/env python3
"""
Step-by-step test to debug the instructor dashboard authentication and course loading.
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    
    try:
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        service = Service(ChromeDriverManager(driver_version="138.0.7204.100").install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Chromium setup failed: {e}")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

def test_auth_debug():
    """Test authentication debug page."""
    driver = setup_driver()
    
    try:
        # Load the auth debug page
        debug_url = "file:///home/bbrelin/course-creator/debug_auth.html"
        print(f"Loading auth debug page: {debug_url}")
        
        driver.get(debug_url)
        time.sleep(2)
        
        # Get debug output
        debug_output = driver.find_element(By.ID, "debug-output").text
        print("Authentication debug output:")
        print(debug_output)
        
        # Check console logs
        logs = driver.get_log('browser')
        for log in logs:
            print(f"Console: {log['message']}")
        
    finally:
        driver.quit()

def test_dashboard_loading():
    """Test dashboard loading step by step."""
    driver = setup_driver()
    
    try:
        # First, inject some test authentication data
        driver.get("about:blank")
        
        # Inject test user data
        driver.execute_script("""
            localStorage.setItem('authToken', 'test-token-123');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 'test-user-id',
                email: 'instructor@example.com',
                full_name: 'Test Instructor',
                role: 'instructor'
            }));
            localStorage.setItem('userEmail', 'instructor@example.com');
        """)
        
        print("Injected test authentication data")
        
        # Now load the instructor dashboard
        dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        print(f"Loading instructor dashboard: {dashboard_url}")
        
        driver.get(dashboard_url)
        time.sleep(5)
        
        # Check what happened
        print("\n=== Browser Console Logs ===")
        logs = driver.get_log('browser')
        for log in logs:
            print(f"{log['level']}: {log['message']}")
        
        # Check if functions are available
        print("\n=== Function Availability ===")
        function_checks = [
            'getCurrentUser',
            'showSection',
            'loadUserCourses',
            'CONFIG'
        ]
        
        for func_name in function_checks:
            try:
                is_available = driver.execute_script(f"return typeof {func_name} !== 'undefined';")
                print(f"{func_name}: {'Available' if is_available else 'Not available'}")
                
                if func_name == 'getCurrentUser' and is_available:
                    user = driver.execute_script("return getCurrentUser();")
                    print(f"  getCurrentUser() returns: {user}")
                    
                if func_name == 'CONFIG' and is_available:
                    endpoints = driver.execute_script("return CONFIG.ENDPOINTS.COURSES;")
                    print(f"  CONFIG.ENDPOINTS.COURSES: {endpoints}")
                    
            except Exception as e:
                print(f"{func_name}: Error checking - {e}")
        
        # Check if course loading was attempted
        print("\n=== Course Loading Check ===")
        try:
            courses = driver.execute_script("return window.userCourses;")
            print(f"userCourses: {courses}")
        except Exception as e:
            print(f"Error getting userCourses: {e}")
        
        # Check page title and basic elements
        print(f"\n=== Page Info ===")
        print(f"Page title: {driver.title}")
        print(f"Page URL: {driver.current_url}")
        
        # Check if main sections exist
        sections = driver.find_elements(By.CSS_SELECTOR, ".content-section")
        print(f"Found {len(sections)} content sections")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("Step 1: Testing authentication debug page...")
    test_auth_debug()
    
    print("\n" + "="*50)
    print("Step 2: Testing dashboard loading with mock auth...")
    test_dashboard_loading()