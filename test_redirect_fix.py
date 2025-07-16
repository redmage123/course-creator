#!/usr/bin/env python3
"""
Test to verify the instructor dashboard redirect fix
"""
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def setup_driver():
    """Setup Chrome driver for testing"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--user-data-dir=/tmp/chrome-test-fix')
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Could not setup browser: {e}")
        return None

def test_redirect_fix():
    """Test that the dashboard loads properly without automatic redirect to overview"""
    print("🧪 Testing Redirect Fix")
    print("=" * 30)
    
    driver = setup_driver()
    if not driver:
        print("❌ Could not setup browser")
        return False
    
    try:
        # Get authentication token
        login_data = {
            "username": "bbrelin@gmail.com",
            "password": "f00bar123"
        }
        
        response = requests.post("http://localhost:8000/auth/login", data=login_data)
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
        
        token = response.json().get('access_token')
        print("✅ Authentication successful")
        
        # Load dashboard
        dashboard_url = "http://localhost:8080/instructor-dashboard.html"
        driver.get(dashboard_url)
        
        # Inject authentication
        driver.execute_script(f"""
            localStorage.setItem('authToken', '{token}');
            localStorage.setItem('currentUser', JSON.stringify({{
                id: 'cd7f5be1-bac8-49cd-8034-0f7ded517efd',
                email: 'bbrelin@gmail.com',
                full_name: 'Braun Brelin',
                role: 'instructor'
            }}));
        """)
        
        # Reload to apply authentication
        driver.refresh()
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-layout")))
        
        print("✅ Dashboard loaded")
        
        # Wait for JavaScript initialization
        time.sleep(2)
        
        # Check which section is active
        active_sections = driver.find_elements(By.CSS_SELECTOR, ".content-section.active")
        print(f"Active sections: {len(active_sections)}")
        
        if len(active_sections) == 1:
            section_id = active_sections[0].get_attribute('id')
            print(f"Active section: {section_id}")
            
            # Check if it's the courses section (what we want)
            if section_id == 'courses-section':
                print("✅ Dashboard shows courses section by default")
                
                # Check if overview is NOT active
                overview_section = driver.find_element(By.ID, "overview-section")
                if 'active' not in overview_section.get_attribute('class'):
                    print("✅ Overview section is NOT automatically active")
                    return True
                else:
                    print("❌ Overview section is still active")
                    return False
            else:
                print(f"❌ Wrong section active: {section_id}")
                return False
        else:
            print(f"❌ Wrong number of active sections: {len(active_sections)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        driver.quit()

def main():
    """Run the test"""
    print("🚀 TESTING REDIRECT FIX")
    print("=" * 40)
    
    success = test_redirect_fix()
    
    if success:
        print("\n✅ Redirect fix successful!")
        print("   Dashboard now loads courses section by default")
        print("   No more automatic redirect to overview")
    else:
        print("\n❌ Redirect fix failed!")
        print("   Dashboard still has redirect issues")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)