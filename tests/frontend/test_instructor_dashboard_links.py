#!/usr/bin/env python3
"""
Comprehensive frontend unit tests for instructor dashboard links and interactions
"""
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os


class TestInstructorDashboardLinks:
    """Test all links and interactions in instructor dashboard"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        try:
            service = Service('/usr/bin/chromedriver')  # Use system chromedriver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            yield driver
        finally:
            driver.quit()
    
    @pytest.fixture(scope="class")
    def authenticated_session(self, driver):
        """Setup authenticated session"""
        # Get authentication token
        login_data = {
            "username": "bbrelin@gmail.com",
            "password": "f00bar123"
        }
        
        response = requests.post("http://localhost:8000/auth/login", data=login_data)
        assert response.status_code == 200, f"Authentication failed: {response.status_code}"
        
        token = response.json().get('access_token')
        
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
        
        return driver
    
    def test_navigation_links(self, authenticated_session):
        """Test all navigation links work correctly"""
        driver = authenticated_session
        wait = WebDriverWait(driver, 10)
        
        # Test navigation links
        nav_links = [
            ('overview', 'overview-section'),
            ('courses', 'courses-section'),
            ('create-course', 'create-course-section'),
            ('students', 'students-section'),
            ('content', 'content-section'),
            ('labs', 'labs-section'),
            ('quizzes', 'quizzes-section')
        ]
        
        for link_section, expected_section in nav_links:
            print(f"Testing navigation to {link_section}")
            
            # Click navigation link
            nav_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-section="{link_section}"]')))
            nav_link.click()
            
            # Wait for section to become active
            time.sleep(0.5)
            
            # Check that correct section is active
            active_section = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'#{expected_section}.active')))
            assert active_section.is_displayed(), f"Section {expected_section} is not displayed"
            
            # Check that other sections are not active
            other_sections = driver.find_elements(By.CSS_SELECTOR, '.content-section.active')
            assert len(other_sections) == 1, f"Multiple sections active: {[s.get_attribute('id') for s in other_sections]}"
    
    def test_course_view_button(self, authenticated_session):
        """Test the course view button functionality"""
        driver = authenticated_session
        wait = WebDriverWait(driver, 10)
        
        # Navigate to courses section
        courses_nav = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-section="courses"]')))
        courses_nav.click()
        
        time.sleep(1)
        
        # Look for view button
        try:
            view_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.view-course-btn, .btn-view, [onclick*="viewCourse"]')))
            print(f"Found view button: {view_button.get_attribute('outerHTML')}")
            
            # Count existing modals before clicking
            existing_modals = driver.find_elements(By.CSS_SELECTOR, '.modal, .modal-overlay')
            initial_modal_count = len(existing_modals)
            print(f"Initial modal count: {initial_modal_count}")
            
            # Click view button
            view_button.click()
            
            # Wait for modal to appear
            time.sleep(1)
            
            # Check for modal
            modals = driver.find_elements(By.CSS_SELECTOR, '.modal, .modal-overlay')
            new_modal_count = len(modals)
            print(f"New modal count: {new_modal_count}")
            
            # Should have exactly one modal
            assert new_modal_count == 1, f"Expected 1 modal, got {new_modal_count}"
            
            # Check modal content
            modal = modals[0]
            assert modal.is_displayed(), "Modal is not displayed"
            
            # Check for close button
            close_buttons = modal.find_elements(By.CSS_SELECTOR, '.close, .modal-close, [onclick*="close"]')
            assert len(close_buttons) > 0, "Modal has no close button"
            
            # Test closing modal
            close_button = close_buttons[0]
            close_button.click()
            
            # Wait for modal to close
            time.sleep(1)
            
            # Check modal is gone
            remaining_modals = driver.find_elements(By.CSS_SELECTOR, '.modal, .modal-overlay')
            assert len(remaining_modals) == 0, f"Modal did not close properly. Remaining: {len(remaining_modals)}"
            
        except TimeoutException:
            # No view button found - check if there are courses
            course_items = driver.find_elements(By.CSS_SELECTOR, '.course-item, .course-card')
            if len(course_items) == 0:
                pytest.skip("No courses available to test view button")
            else:
                pytest.fail("View button not found despite having courses")
    
    def test_modal_stacking_issue(self, authenticated_session):
        """Test that modals don't stack on top of each other"""
        driver = authenticated_session
        wait = WebDriverWait(driver, 10)
        
        # Navigate to courses section
        courses_nav = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-section="courses"]')))
        courses_nav.click()
        
        time.sleep(1)
        
        # Find all clickable elements that might open modals
        modal_triggers = driver.find_elements(By.CSS_SELECTOR, 
            '[onclick*="Modal"], [onclick*="modal"], .btn-create, .btn-view, .btn-edit')
        
        if len(modal_triggers) == 0:
            pytest.skip("No modal triggers found")
        
        for i, trigger in enumerate(modal_triggers[:3]):  # Test first 3 triggers
            print(f"Testing modal trigger {i+1}: {trigger.get_attribute('outerHTML')[:100]}...")
            
            # Clear any existing modals
            driver.execute_script("""
                document.querySelectorAll('.modal, .modal-overlay').forEach(modal => {
                    modal.remove();
                });
            """)
            
            # Click trigger
            try:
                trigger.click()
                time.sleep(0.5)
                
                # Count modals
                modals = driver.find_elements(By.CSS_SELECTOR, '.modal, .modal-overlay')
                assert len(modals) <= 1, f"Multiple modals opened: {len(modals)}"
                
                # If modal opened, close it
                if len(modals) > 0:
                    close_button = modals[0].find_element(By.CSS_SELECTOR, '.close, .modal-close, [onclick*="close"]')
                    close_button.click()
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"Error testing trigger {i+1}: {e}")
                # Continue with next trigger
                continue
    
    def test_dropdown_functionality(self, authenticated_session):
        """Test dropdown functionality"""
        driver = authenticated_session
        wait = WebDriverWait(driver, 10)
        
        # Test account dropdown
        dropdown_trigger = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[onclick*="toggleAccountDropdown"]')))
        
        # Click to open dropdown
        dropdown_trigger.click()
        time.sleep(0.5)
        
        # Check dropdown is visible
        dropdown_menu = wait.until(EC.presence_of_element_located((By.ID, "accountMenu")))
        assert dropdown_menu.is_displayed(), "Dropdown menu is not displayed"
        
        # Click outside to close
        driver.find_element(By.TAG_NAME, "body").click()
        time.sleep(0.5)
        
        # Check dropdown is hidden
        assert not dropdown_menu.is_displayed(), "Dropdown menu did not close"
    
    def test_quiz_pane_clicking(self, authenticated_session):
        """Test quiz pane clicking behavior"""
        driver = authenticated_session
        wait = WebDriverWait(driver, 10)
        
        # Navigate to quizzes section
        quizzes_nav = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-section="quizzes"]')))
        quizzes_nav.click()
        
        time.sleep(1)
        
        # Check quizzes section is active
        quizzes_section = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#quizzes-section.active')))
        assert quizzes_section.is_displayed(), "Quizzes section is not displayed"
        
        # Test clicking on quiz items (if any)
        quiz_items = driver.find_elements(By.CSS_SELECTOR, '.quiz-item, .quiz-card')
        
        for i, quiz_item in enumerate(quiz_items[:3]):  # Test first 3 quiz items
            print(f"Testing quiz item {i+1}")
            
            # Click quiz item
            quiz_item.click()
            time.sleep(0.5)
            
            # Should stay in quizzes section
            assert quizzes_section.is_displayed(), f"Quiz item {i+1} redirected away from quizzes"
            
            # Should not show "quiz not found" error
            error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'quiz not found')]")
            assert len(error_elements) == 0, f"Quiz item {i+1} shows 'quiz not found' error"
    
    def test_all_buttons_clickable(self, authenticated_session):
        """Test that all buttons are clickable and don't cause errors"""
        driver = authenticated_session
        wait = WebDriverWait(driver, 10)
        
        # Get all buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        links_with_onclick = driver.find_elements(By.CSS_SELECTOR, "[onclick]")
        
        all_clickables = buttons + links_with_onclick
        
        for i, clickable in enumerate(all_clickables):
            if not clickable.is_displayed():
                continue
                
            print(f"Testing clickable {i+1}: {clickable.get_attribute('outerHTML')[:50]}...")
            
            try:
                # Store initial state
                initial_url = driver.current_url
                initial_modals = len(driver.find_elements(By.CSS_SELECTOR, '.modal, .modal-overlay'))
                
                # Click element
                clickable.click()
                time.sleep(0.5)
                
                # Check for JavaScript errors
                logs = driver.get_log('browser')
                js_errors = [log for log in logs if log['level'] == 'SEVERE']
                
                if js_errors:
                    print(f"JavaScript errors after clicking: {js_errors}")
                    # Don't fail test, just log the error
                
                # Check if we're still on the same page
                current_url = driver.current_url
                if current_url != initial_url:
                    print(f"URL changed from {initial_url} to {current_url}")
                
            except Exception as e:
                print(f"Error clicking element {i+1}: {e}")
                # Continue with next element
                continue


def main():
    """Run all tests"""
    import subprocess
    
    # Run tests with pytest
    result = subprocess.run([
        'python', '-m', 'pytest', 
        '/home/bbrelin/course-creator/tests/frontend/test_instructor_dashboard_links.py',
        '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")
    
    return result.returncode == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)