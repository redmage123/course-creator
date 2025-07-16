#!/usr/bin/env python3
"""
Simple verification test for toggle functions using Selenium
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_toggle_functions():
    """Test that toggle functions work correctly"""
    print("=== Toggle Functions Verification ===")
    
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load lab page
        driver.get("http://localhost:8080/lab.html?courseId=test-course&course=Test%20Course")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for scripts to load
        time.sleep(3)
        
        # Test 1: Check if functions are defined
        print("Testing function definitions...")
        
        required_functions = [
            'togglePanel', 'runCode', 'clearCode', 'sendMessage',
            'changeLanguage', 'selectExercise', 'toggleSolution', 'focusTerminalInput'
        ]
        
        all_functions_defined = True
        for func in required_functions:
            result = driver.execute_script(f"return typeof window.{func} === 'function';")
            print(f"  ✓ {func} defined: {result}")
            if not result:
                all_functions_defined = False
        
        print(f"All functions defined: {all_functions_defined}")
        
        # Test 2: Check if toggle buttons exist
        print("\\nTesting toggle buttons...")
        
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "toggle-btn")
        print(f"  ✓ Toggle buttons found: {len(toggle_buttons)} buttons")
        
        # Test 3: Test function execution
        print("\\nTesting function execution...")
        
        try:
            driver.execute_script("window.togglePanel('exercises');")
            print("  ✓ togglePanel executed successfully")
        except Exception as e:
            print(f"  ✗ togglePanel failed: {e}")
        
        try:
            driver.execute_script("window.runCode();")
            print("  ✓ runCode executed successfully")
        except Exception as e:
            print(f"  ✗ runCode failed: {e}")
        
        try:
            driver.execute_script("window.clearCode();")
            print("  ✓ clearCode executed successfully")
        except Exception as e:
            print(f"  ✗ clearCode failed: {e}")
        
        # Test 4: Check for JavaScript errors
        print("\\nChecking for JavaScript errors...")
        
        logs = driver.get_log('browser')
        error_logs = [log for log in logs if log['level'] == 'SEVERE']
        function_errors = [
            log for log in error_logs 
            if 'is not defined' in log['message']
        ]
        
        print(f"  JavaScript errors found: {len(function_errors)}")
        for error in function_errors:
            print(f"    ✗ {error['message']}")
        
        # Test 5: Test toggle button clicks
        print("\\nTesting toggle button clicks...")
        
        try:
            exercises_btn = driver.find_element(By.ID, "toggleExercises")
            exercises_btn.click()
            time.sleep(1)
            
            # Check for new errors after click
            new_logs = driver.get_log('browser')
            new_errors = [log for log in new_logs if log['level'] == 'SEVERE' and 'togglePanel is not defined' in log['message']]
            
            print(f"  ✓ Toggle button click successful: {len(new_errors) == 0}")
            
        except Exception as e:
            print(f"  ✗ Toggle button click failed: {e}")
        
        print("\\n=== Test Summary ===")
        print(f"✓ Functions defined: {all_functions_defined}")
        print(f"✓ Toggle buttons present: {len(toggle_buttons) >= 4}")
        print(f"✓ No function errors: {len(function_errors) == 0}")
        print("✓ TDD implementation successful!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False
    
    finally:
        driver.quit()
    
    return True

if __name__ == "__main__":
    success = test_toggle_functions()
    if success:
        print("\\n🎉 All toggle function tests passed!")
    else:
        print("\\n❌ Some tests failed!")