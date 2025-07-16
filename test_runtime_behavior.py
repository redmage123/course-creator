#!/usr/bin/env python3
"""
Test to detect runtime behavior causing automatic redirect
"""
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

def setup_driver():
    """Setup Chrome driver"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--user-data-dir=/tmp/chrome-test-runtime')
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Could not setup browser: {e}")
        return None

def test_runtime_redirect():
    """Test if there's a runtime redirect happening"""
    print("🧪 Testing Runtime Redirect Behavior")
    print("=" * 45)
    
    driver = setup_driver()
    if not driver:
        print("❌ Could not setup browser for testing")
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
        dashboard_url = "file:///home/bbrelin/course-creator/frontend/instructor-dashboard.html"
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
        
        # Check initial state (should be no automatic redirect)
        time.sleep(1)
        
        # Check what sections are active immediately after load
        active_sections = driver.find_elements(By.CSS_SELECTOR, ".content-section.active")
        print(f"Active sections immediately after load: {len(active_sections)}")
        
        for section in active_sections:
            section_id = section.get_attribute('id')
            print(f"  - {section_id}")
        
        # Wait a bit more to see if there's a delayed redirect
        time.sleep(3)
        
        # Check again after a delay
        active_sections_after = driver.find_elements(By.CSS_SELECTOR, ".content-section.active")
        print(f"Active sections after 3 seconds: {len(active_sections_after)}")
        
        for section in active_sections_after:
            section_id = section.get_attribute('id')
            print(f"  - {section_id}")
        
        # Check for any JavaScript console logs that might indicate redirects
        logs = driver.get_log('browser')
        for log in logs:
            if 'showSection' in log['message'] or 'overview' in log['message']:
                print(f"📋 Console log: {log['message']}")
        
        # Check if there's any automatic navigation happening
        # Look for patterns that indicate automatic redirect
        if len(active_sections) != len(active_sections_after):
            print("❌ Number of active sections changed - indicates automatic redirect")
            return False
        
        # Check if the same sections are active
        initial_ids = {section.get_attribute('id') for section in active_sections}
        after_ids = {section.get_attribute('id') for section in active_sections_after}
        
        if initial_ids != after_ids:
            print("❌ Different sections became active - indicates automatic redirect")
            print(f"  Initial: {initial_ids}")
            print(f"  After: {after_ids}")
            return False
        
        print("✅ No automatic redirect detected")
        return True
        
    except Exception as e:
        print(f"❌ Runtime test failed: {e}")
        return False
    finally:
        driver.quit()

def test_modular_js_conflict():
    """Test if modular JS is conflicting with inline JS"""
    print("\n🧪 Testing Modular JS Conflict")
    print("=" * 45)
    
    # Check if both modular and inline systems are defining showSection
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
        
        # Check for modular JS import
        has_modular_js = 'main-modular.js' in content
        print(f"Has modular JS: {has_modular_js}")
        
        # Check for inline showSection definition
        has_inline_showsection = 'window.showSection = function' in content
        print(f"Has inline showSection: {has_inline_showsection}")
        
        # Check for instructor-dashboard.js module
        has_instructor_module = 'instructor-dashboard.js' in content
        print(f"Has instructor module: {has_instructor_module}")
        
        if has_modular_js and has_inline_showsection:
            print("⚠️  Potential conflict: Both modular and inline JS systems present")
            print("   This could cause function redefinition issues")
            
            # Check if there are multiple definitions
            showsection_count = content.count('showSection')
            print(f"   showSection mentioned {showsection_count} times")
            
            if showsection_count > 20:  # Threshold for too many mentions
                print("❌ Too many showSection references - likely causing conflicts")
                return False
        
        print("✅ No obvious JS conflicts detected")
        return True
        
    except Exception as e:
        print(f"❌ JS conflict test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 TESTING RUNTIME BEHAVIOR")
    print("=" * 50)
    
    test1 = test_runtime_redirect()
    test2 = test_modular_js_conflict()
    
    if test1 and test2:
        print("\n✅ Tests suggest the issue is not runtime redirect")
        print("   The problem may be elsewhere...")
    else:
        print("\n❌ Tests detected runtime issues!")
        print("   This explains why static tests miss the problem")
    
    return test1 and test2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)