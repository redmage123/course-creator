#!/usr/bin/env python3
"""
Test the course view fix to ensure the buttons work properly
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

def setup_driver():
    """Setup Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--user-data-dir=/tmp/chrome-test-course-view')
    
    try:
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Chromium setup failed: {e}")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

def test_course_view_buttons():
    """Test that the course view buttons work properly"""
    
    print("Testing course view button functionality...")
    
    # Get authentication token for bbrelin
    login_data = {
        "username": "bbrelin@gmail.com",
        "password": "f00bar123"
    }
    
    response = requests.post("http://localhost:8000/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return False
    
    token = response.json().get('access_token')
    print(f"✅ Successfully authenticated bbrelin")
    
    # Setup driver
    driver = setup_driver()
    
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
        
        # Load the instructor dashboard
        dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        driver.get(dashboard_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Click on My Courses
        try:
            courses_link = driver.find_element(By.XPATH, "//a[contains(@onclick, 'courses')]")
            courses_link.click()
            print("✅ Successfully clicked on My Courses")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Failed to click My Courses: {e}")
            return False
        
        # Check if courses are displayed
        try:
            course_cards = driver.find_elements(By.CLASS_NAME, "course-card")
            print(f"✅ Found {len(course_cards)} course cards")
            
            if len(course_cards) == 0:
                print("❌ No course cards found")
                return False
            
            # Test the first course card
            course_card = course_cards[0]
            
            # Check if action buttons are horizontal
            actions_div = course_card.find_element(By.CLASS_NAME, "course-actions")
            actions_style = actions_div.get_attribute("style")
            print(f"Course actions style: {actions_style}")
            
            if "display: flex" in actions_style:
                print("✅ Action buttons are set to horizontal layout")
            else:
                print("❌ Action buttons are not horizontal")
                return False
            
            # Test View button
            try:
                view_button = course_card.find_element(By.XPATH, ".//button[contains(text(), 'View')]")
                print("✅ Found View button")
                
                # Click the view button
                view_button.click()
                print("✅ Successfully clicked View button")
                time.sleep(2)
                
                # Check if modal appeared
                try:
                    modal = driver.find_element(By.CLASS_NAME, "modal")
                    print("✅ Modal appeared after clicking View")
                    
                    # Check modal content
                    modal_content = modal.find_element(By.CLASS_NAME, "modal-content")
                    modal_text = modal_content.text
                    if "Introduction to Python" in modal_text:
                        print("✅ Modal shows correct course information")
                    else:
                        print("❌ Modal does not show correct course information")
                        return False
                    
                    # Close modal
                    close_button = modal.find_element(By.CLASS_NAME, "close-btn")
                    close_button.click()
                    print("✅ Successfully closed modal")
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Modal did not appear or has issues: {e}")
                    return False
                
            except Exception as e:
                print(f"❌ View button not found or not clickable: {e}")
                return False
            
            # Test Edit Content button
            try:
                edit_button = course_card.find_element(By.XPATH, ".//button[contains(text(), 'Edit Content')]")
                print("✅ Found Edit Content button")
                
                # Click the edit button
                edit_button.click()
                print("✅ Successfully clicked Edit Content button")
                time.sleep(2)
                
                # Check if it navigated to content section
                current_url = driver.current_url
                print(f"Current URL after Edit Content: {current_url}")
                
            except Exception as e:
                print(f"❌ Edit Content button not found or not clickable: {e}")
                return False
            
            # Test Delete button (but don't actually delete)
            try:
                delete_button = course_card.find_element(By.XPATH, ".//button[contains(text(), 'Delete')]")
                print("✅ Found Delete button")
                
                # We won't actually click delete to avoid deleting the course
                print("✅ Delete button is present (not clicking to preserve course)")
                
            except Exception as e:
                print(f"❌ Delete button not found: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to find course cards: {e}")
            return False
        
        print("🎉 All course view button tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        driver.quit()

if __name__ == "__main__":
    success = test_course_view_buttons()
    if success:
        print("\n✅ FRONTEND TEST PASSED: Course view buttons work correctly!")
    else:
        print("\n❌ FRONTEND TEST FAILED: Course view buttons have issues!")