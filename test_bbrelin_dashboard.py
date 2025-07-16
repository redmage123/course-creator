#!/usr/bin/env python3
"""
Test instructor dashboard with bbrelin user credentials
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
    chrome_options.add_argument('--user-data-dir=/tmp/chrome-test-bbrelin')
    
    try:
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        service = Service(ChromeDriverManager(driver_version="138.0.7204.100").install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Chromium setup failed: {e}")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

def test_bbrelin_authentication():
    """Test if bbrelin user can authenticate"""
    print("Testing bbrelin authentication...")
    
    # Use the known password
    login_data = {
        "username": "bbrelin@gmail.com",
        "password": "P0stgr3s:atao12e"
    }
    
    try:
        response = requests.post("http://localhost:8000/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"✅ Successfully authenticated bbrelin")
            print(f"Token: {token[:50]}...")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error authenticating: {e}")
    
    return None

def test_bbrelin_dashboard():
    """Test dashboard with bbrelin user"""
    
    # Try to authenticate bbrelin
    token = test_bbrelin_authentication()
    if not token:
        print("❌ Cannot test dashboard - authentication failed")
        return
    
    # Setup driver
    driver = setup_driver()
    
    try:
        # First load a blank page
        driver.get("about:blank")
        
        # Inject authentication data for bbrelin
        driver.execute_script(f"""
            localStorage.setItem('authToken', '{token}');
            localStorage.setItem('currentUser', JSON.stringify({{
                id: 'cd7f5be1-bac8-49cd-8034-0f7ded517efd',
                email: 'bbrelin@gmail.com',
                full_name: 'Braun Brelin',
                role: 'instructor'
            }}));
            localStorage.setItem('userEmail', 'bbrelin@gmail.com');
        """)
        
        print("✅ Injected bbrelin authentication data")
        
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
            print(f"✅ SUCCESS: Bbrelin sees {len(user_courses)} courses!")
            for course in user_courses:
                print(f"  - {course.get('title', 'Unknown')}")
                
            # Check if Introduction to Python is there
            course_titles = [course.get('title', '') for course in user_courses]
            if "Introduction to Python" in course_titles:
                print("🎉 SUCCESS: Introduction to Python course is showing for bbrelin!")
            else:
                print("❌ Introduction to Python course not found in bbrelin's courses")
                
        else:
            print("❌ No courses found for bbrelin in dashboard")
        
        # Test the courses API directly
        print("\n=== Direct API Test ===")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        api_response = requests.get("http://localhost:8004/courses", headers=headers)
        if api_response.status_code == 200:
            api_courses = api_response.json()
            print(f"✅ API returns {len(api_courses)} courses for bbrelin")
            for course in api_courses:
                print(f"  - {course.get('title', 'Unknown')}")
        else:
            print(f"❌ API call failed: {api_response.status_code}")
        
        # Take a screenshot for verification
        driver.save_screenshot("bbrelin_dashboard_test.png")
        print("📸 Screenshot saved as bbrelin_dashboard_test.png")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_bbrelin_dashboard()