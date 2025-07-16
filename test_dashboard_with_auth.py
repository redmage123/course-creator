#!/usr/bin/env python3
"""
Test instructor dashboard with valid authentication
"""
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup Chrome driver."""
    chrome_options = Options()
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

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "username": "instructor@courseplatform.com",
        "password": "Instructor123!"
    }
    
    response = requests.post("http://localhost:8000/auth/login", data=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get('access_token')
    return None

def test_dashboard_with_auth():
    """Test dashboard with valid authentication"""
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    print(f"✅ Got auth token: {token[:50]}...")
    
    # Setup driver
    driver = setup_driver()
    
    try:
        # First load a blank page
        driver.get("about:blank")
        
        # Inject authentication data
        driver.execute_script(f"""
            localStorage.setItem('authToken', '{token}');
            localStorage.setItem('currentUser', JSON.stringify({{
                id: 'fb499059-fd8f-4254-bf82-8a5117abe2cb',
                email: 'instructor@courseplatform.com',
                full_name: 'Test Instructor',
                role: 'instructor'
            }}));
            localStorage.setItem('userEmail', 'instructor@courseplatform.com');
        """)
        
        print("✅ Injected authentication data")
        
        # Now load the instructor dashboard
        dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        print(f"Loading dashboard: {dashboard_url}")
        
        driver.get(dashboard_url)
        time.sleep(5)
        
        # Check browser console
        print("\n=== Browser Console Logs ===")
        logs = driver.get_log('browser')
        for log in logs:
            print(f"{log['level']}: {log['message']}")
        
        # Check if functions are available
        print("\n=== Function Check ===")
        get_current_user = driver.execute_script("return typeof getCurrentUser !== 'undefined' && getCurrentUser();")
        print(f"getCurrentUser(): {get_current_user}")
        
        user_courses = driver.execute_script("return window.userCourses;")
        print(f"userCourses: {user_courses}")
        
        # Check if course loading worked
        if user_courses and len(user_courses) > 0:
            print(f"✅ SUCCESS: Found {len(user_courses)} courses!")
            for course in user_courses:
                print(f"  - {course.get('title', 'Unknown')}")
        else:
            print("❌ No courses found in dashboard")
        
        # Take a screenshot for manual verification
        driver.save_screenshot("instructor_dashboard_test.png")
        print("📸 Screenshot saved as instructor_dashboard_test.png")
        
        # Check page content
        page_text = driver.find_element(By.TAG_NAME, "body").text
        if "Introduction to Python" in page_text or "Java Fundamentals" in page_text:
            print("✅ Course names found in page content!")
        else:
            print("❌ Course names not found in page content")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    test_dashboard_with_auth()