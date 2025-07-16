#!/usr/bin/env python3
"""
Comprehensive test for the instructor dashboard fixes
"""
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json

def setup_driver():
    """Setup Chrome driver with proper options."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--user-data-dir=/tmp/chrome-test-dashboard-fixes')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--silent')
    
    try:
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Chrome setup failed: {e}")
        return None

def test_authentication():
    """Test 1: Authentication works"""
    print("🧪 TEST 1: Authentication")
    
    login_data = {
        "username": "bbrelin@gmail.com",
        "password": "f00bar123"
    }
    
    try:
        response = requests.post("http://localhost:8000/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json().get('access_token')
            print("✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_courses_api(token):
    """Test 2: Courses API returns data"""
    print("\n🧪 TEST 2: Courses API")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("http://localhost:8004/courses", headers=headers)
        if response.status_code == 200:
            courses = response.json()
            if len(courses) > 0:
                print(f"✅ API returned {len(courses)} courses")
                print(f"  Course: {courses[0].get('title', 'Unknown')}")
                return courses
            else:
                print("❌ API returned no courses")
                return []
        else:
            print(f"❌ API failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ API error: {e}")
        return []

def test_dashboard_loads(token):
    """Test 3: Dashboard loads without errors"""
    print("\n🧪 TEST 3: Dashboard Loading")
    
    driver = setup_driver()
    if not driver:
        print("❌ Could not setup Chrome driver")
        return False
    
    try:
        # Load blank page first
        driver.get("about:blank")
        
        # Inject authentication
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
        
        # Load dashboard
        dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        driver.get(dashboard_url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-layout")))
        
        print("✅ Dashboard loaded successfully")
        
        # Check for JavaScript errors
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if errors:
            print(f"❌ Found {len(errors)} JavaScript errors:")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  - {error['message']}")
            return False
        else:
            print("✅ No JavaScript errors found")
            return True
            
    except Exception as e:
        print(f"❌ Dashboard loading error: {e}")
        return False
    finally:
        driver.quit()

def test_courses_section_navigation(token):
    """Test 4: Courses section navigation"""
    print("\n🧪 TEST 4: Courses Section Navigation")
    
    driver = setup_driver()
    if not driver:
        print("❌ Could not setup Chrome driver")
        return False
    
    try:
        # Load and authenticate
        driver.get("about:blank")
        driver.execute_script(f"""
            localStorage.setItem('authToken', '{token}');
            localStorage.setItem('currentUser', JSON.stringify({{
                id: 'cd7f5be1-bac8-49cd-8034-0f7ded517efd',
                email: 'bbrelin@gmail.com',
                full_name: 'Braun Brelin',
                role: 'instructor'
            }}));
        """)
        
        dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        driver.get(dashboard_url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-layout")))
        
        # Wait for courses to load
        time.sleep(3)
        
        # Find and click "My Courses" link
        try:
            courses_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-section='courses']")))
            courses_link.click()
            print("✅ Successfully clicked 'My Courses'")
            
            # Wait for courses section to appear
            time.sleep(2)
            
            # Check if courses section is visible
            courses_section = driver.find_element(By.ID, "courses-section")
            if courses_section.is_displayed():
                print("✅ Courses section is visible")
                
                # Check for course cards
                try:
                    course_cards = driver.find_elements(By.CLASS_NAME, "course-card")
                    if len(course_cards) > 0:
                        print(f"✅ Found {len(course_cards)} course cards")
                        return True
                    else:
                        print("❌ No course cards found")
                        return False
                except Exception as e:
                    print(f"❌ Error finding course cards: {e}")
                    return False
            else:
                print("❌ Courses section is not visible")
                return False
                
        except Exception as e:
            print(f"❌ Error clicking 'My Courses': {e}")
            return False
            
    except Exception as e:
        print(f"❌ Navigation test error: {e}")
        return False
    finally:
        driver.quit()

def test_course_view_button(token):
    """Test 5: Course View button functionality"""
    print("\n🧪 TEST 5: Course View Button")
    
    driver = setup_driver()
    if not driver:
        print("❌ Could not setup Chrome driver")
        return False
    
    try:
        # Load and authenticate
        driver.get("about:blank")
        driver.execute_script(f"""
            localStorage.setItem('authToken', '{token}');
            localStorage.setItem('currentUser', JSON.stringify({{
                id: 'cd7f5be1-bac8-49cd-8a43-350c07a0f24b',
                email: 'bbrelin@gmail.com',
                full_name: 'Braun Brelin',
                role: 'instructor'
            }}));
        """)
        
        dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        driver.get(dashboard_url)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-layout")))
        
        # Wait for courses to load
        time.sleep(3)
        
        # Click My Courses
        courses_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-section='courses']")))
        courses_link.click()
        time.sleep(2)
        
        # Find course card and view button
        try:
            view_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View')]")))
            print("✅ Found View button")
            
            # Click the view button
            view_button.click()
            print("✅ Successfully clicked View button")
            
            # Wait for modal to appear
            time.sleep(2)
            
            # Check if modal appeared
            try:
                modal = driver.find_element(By.CLASS_NAME, "modal")
                if modal.is_displayed():
                    print("✅ Modal appeared")
                    
                    # Check modal content
                    modal_text = modal.text
                    if "Introduction to Python" in modal_text:
                        print("✅ Modal shows correct course information")
                        return True
                    else:
                        print("❌ Modal does not show correct course information")
                        return False
                else:
                    print("❌ Modal is not visible")
                    return False
            except NoSuchElementException:
                print("❌ Modal did not appear")
                return False
                
        except Exception as e:
            print(f"❌ Error with View button: {e}")
            return False
            
    except Exception as e:
        print(f"❌ View button test error: {e}")
        return False
    finally:
        driver.quit()

def test_javascript_functions():
    """Test 6: JavaScript functions are defined"""
    print("\n🧪 TEST 6: JavaScript Functions")
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
        
        required_functions = [
            'viewCourseDetails',
            'confirmDeleteCourse',
            'deleteCourse',
            'updateCoursesDisplay',
            'closeCreateLabModal',
            'toggleAccountDropdown',
            'logout'
        ]
        
        all_found = True
        for func in required_functions:
            if f'window.{func}' in content:
                print(f"✅ Found function: {func}")
            else:
                print(f"❌ Missing function: {func}")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Error checking functions: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 TESTING INSTRUCTOR DASHBOARD FIXES")
    print("=" * 50)
    
    # Test 1: Authentication
    token = test_authentication()
    if not token:
        print("❌ Cannot continue without authentication")
        return False
    
    # Test 2: API
    courses = test_courses_api(token)
    if not courses:
        print("❌ Cannot test dashboard without courses")
        return False
    
    # Test 3: Dashboard loading
    dashboard_loads = test_dashboard_loads(token)
    
    # Test 4: Navigation
    navigation_works = test_courses_section_navigation(token)
    
    # Test 5: View button
    view_button_works = test_course_view_button(token)
    
    # Test 6: JavaScript functions
    functions_defined = test_javascript_functions()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Authentication", token is not None),
        ("Courses API", len(courses) > 0),
        ("Dashboard Loading", dashboard_loads),
        ("Navigation", navigation_works),
        ("View Button", view_button_works),
        ("JavaScript Functions", functions_defined)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL TESTS PASSED! Dashboard fixes are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Dashboard fixes need more work.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)