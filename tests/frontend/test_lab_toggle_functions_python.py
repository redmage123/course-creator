#!/usr/bin/env python3
"""
TDD Test for Lab Toggle Functions - Python Version
Tests that all toggle functions are properly defined and accessible
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.fixture(scope="module")
def driver():
    """Setup Chrome driver for testing"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()


def test_lab_page_loads(driver):
    """Test that the lab page loads successfully"""
    driver.get("http://localhost:8080/lab.html?courseId=test-course&course=Test%20Course")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Wait for scripts to load
    time.sleep(3)
    
    assert "Lab Environment" in driver.title or "Lab" in driver.title


def test_all_toggle_functions_are_defined(driver):
    """Test that all required toggle functions are defined"""
    driver.get("http://localhost:8080/lab.html?courseId=test-course&course=Test%20Course")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Wait for scripts to load
    time.sleep(3)
    
    required_functions = [
        'togglePanel', 'runCode', 'clearCode', 'sendMessage',
        'changeLanguage', 'selectExercise', 'toggleSolution', 'focusTerminalInput',
        'displayExercises', 'forceDisplayExercises', 'showLabNotesModal',
        'updateAIAssistantContext'
    ]
    
    for func in required_functions:
        result = driver.execute_script(f"return typeof window.{func} === 'function';")
        assert result, f"Function {func} should be defined but is not"
        print(f"✓ {func} function is properly defined")


def test_toggle_buttons_exist(driver):
    """Test that toggle buttons exist on the page"""
    driver.get("http://localhost:8080/lab.html?courseId=test-course&course=Test%20Course")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Wait for scripts to load
    time.sleep(3)
    
    toggle_buttons = driver.find_elements(By.CLASS_NAME, "toggle-btn")
    assert len(toggle_buttons) >= 4, f"Expected at least 4 toggle buttons, found {len(toggle_buttons)}"
    print(f"✓ Found {len(toggle_buttons)} toggle buttons")


def test_toggle_function_execution(driver):
    """Test that toggle functions can be executed without errors"""
    driver.get("http://localhost:8080/lab.html?courseId=test-course&course=Test%20Course")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Wait for scripts to load
    time.sleep(3)
    
    # Test basic function calls
    try:
        driver.execute_script("window.togglePanel('exercises');")
        print("✓ togglePanel executed successfully")
    except Exception as e:
        pytest.fail(f"togglePanel failed: {e}")
    
    try:
        driver.execute_script("window.runCode();")
        print("✓ runCode executed successfully")
    except Exception as e:
        pytest.fail(f"runCode failed: {e}")
    
    try:
        driver.execute_script("window.clearCode();")
        print("✓ clearCode executed successfully")
    except Exception as e:
        pytest.fail(f"clearCode failed: {e}")


def test_no_javascript_errors(driver):
    """Test that there are no JavaScript errors on page load"""
    driver.get("http://localhost:8080/lab.html?courseId=test-course&course=Test%20Course")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Wait for scripts to load
    time.sleep(3)
    
    # Check for JavaScript errors
    logs = driver.get_log('browser')
    error_logs = [log for log in logs if log['level'] == 'SEVERE']
    function_errors = [
        log for log in error_logs 
        if 'is not defined' in log['message'] or 'ReferenceError' in log['message']
    ]
    
    assert len(function_errors) == 0, f"Found JavaScript errors: {[err['message'] for err in function_errors]}"
    print("✓ No JavaScript function errors found")


def test_toggle_button_clicks(driver):
    """Test that toggle buttons can be clicked without errors"""
    driver.get("http://localhost:8080/lab.html?courseId=test-course&course=Test%20Course")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Wait for scripts to load
    time.sleep(3)
    
    # Try to click toggle buttons
    try:
        exercises_btn = driver.find_element(By.ID, "toggleExercises")
        exercises_btn.click()
        time.sleep(1)
        
        # Check for new errors after click
        new_logs = driver.get_log('browser')
        new_errors = [log for log in new_logs if log['level'] == 'SEVERE' and 'togglePanel is not defined' in log['message']]
        
        assert len(new_errors) == 0, f"Toggle button click caused errors: {[err['message'] for err in new_errors]}"
        print("✓ Toggle button clicks work without errors")
        
    except Exception as e:
        pytest.fail(f"Toggle button click failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])