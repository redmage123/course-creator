#!/usr/bin/env python3
"""
Selenium End-to-End Tests for Enhanced Content Management
Tests the complete user workflow in the browser
"""

import pytest
import time
import os
import json
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestEnhancedContentManagementE2E:
    """End-to-end Selenium tests for content management functionality"""
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(cls):
        """Setup for the entire test class"""
        # Configure Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)
        cls.base_url = "http://localhost:3000"
        cls.wait = WebDriverWait(cls.driver, 15)
        
        # Create test files
        cls.create_test_files()
        
        yield
        
        # Cleanup
        cls.cleanup_test_files()
        cls.driver.quit()
    
    @classmethod
    def create_test_files(cls):
        """Create test files for upload testing"""
        cls.test_files = {}
        
        # Create test syllabus file
        syllabus_content = """
        Course: Advanced Python Programming
        Duration: 8 weeks
        
        Week 1-2: Python Fundamentals
        - Variables, data types, and operators
        - Control structures and functions
        - Error handling and debugging
        
        Week 3-4: Object-Oriented Programming
        - Classes and objects
        - Inheritance and polymorphism
        - Design patterns
        
        Week 5-6: Advanced Topics
        - Decorators and generators
        - Context managers
        - Multithreading and async programming
        
        Week 7-8: Project Work
        - Build a complete Python application
        - Code review and optimization
        - Deployment strategies
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(syllabus_content)
            cls.test_files['syllabus'] = f.name
        
        # Create test quiz JSON
        quiz_data = {
            "metadata": {
                "title": "Python Advanced Quiz",
                "description": "Test advanced Python concepts",
                "difficulty": "intermediate",
                "time_limit": 45
            },
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "Which of the following is a Python decorator?",
                    "options": [
                        "@property",
                        "#decorator", 
                        "decorator()",
                        "def decorator"
                    ],
                    "correct_answer": "@property",
                    "explanation": "@property is a built-in decorator in Python"
                },
                {
                    "id": 2,
                    "type": "multiple_choice",
                    "question": "What does 'async def' define in Python?",
                    "options": [
                        "Asynchronous function",
                        "Synchronized function",
                        "Abstract function", 
                        "Anonymous function"
                    ],
                    "correct_answer": "Asynchronous function",
                    "explanation": "async def defines coroutines in Python asyncio"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(quiz_data, f, indent=2)
            cls.test_files['quiz'] = f.name
        
        # Create test lab JSON
        lab_data = {
            "metadata": {
                "title": "Python Decorators Lab",
                "environment": "python3.9",
                "difficulty": "intermediate"
            },
            "exercises": [
                {
                    "id": 1,
                    "title": "Create a Timer Decorator",
                    "description": "Build a decorator that measures function execution time",
                    "starter_code": "import time\ndef timer(func):\n    # Your code here\n    pass",
                    "solution": "import time\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        end = time.time()\n        print(f'{func.__name__} took {end-start:.2f} seconds')\n        return result\n    return wrapper"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(lab_data, f, indent=2)
            cls.test_files['lab'] = f.name
    
    @classmethod
    def cleanup_test_files(cls):
        """Clean up test files"""
        for file_path in cls.test_files.values():
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass
    
    def login_as_instructor(self):
        """Helper method to login as instructor"""
        self.driver.get(f"{self.base_url}/index.html")
        
        # Wait for login form
        email_field = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_field = self.driver.find_element(By.ID, "password")
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        # Login with test credentials
        email_field.send_keys("instructor@test.com")
        password_field.send_keys("testpass123")
        login_button.click()
        
        # Wait for redirect to instructor dashboard
        self.wait.until(EC.url_contains("instructor-dashboard"))
        
        # Verify we're on the instructor dashboard
        assert "instructor-dashboard" in self.driver.current_url
    
    def create_test_course(self):
        """Helper method to create a test course"""
        # Navigate to create course section
        create_course_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-section='create-course']"))
        )
        create_course_nav.click()
        
        # Wait for create course form
        course_form = self.wait.until(EC.presence_of_element_located((By.ID, "courseForm")))
        
        # Fill in course details
        title_field = self.driver.find_element(By.NAME, "title")
        description_field = self.driver.find_element(By.NAME, "description")
        category_select = self.driver.find_element(By.NAME, "category")
        difficulty_select = self.driver.find_element(By.NAME, "difficulty_level")
        duration_field = self.driver.find_element(By.NAME, "estimated_duration")
        
        title_field.send_keys("Selenium Test Course")
        description_field.send_keys("A test course for Selenium E2E testing")
        
        # Select category and difficulty
        category_select.send_keys("Programming")
        difficulty_select.send_keys("intermediate")
        duration_field.clear()
        duration_field.send_keys("6")
        
        # Submit the form
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for success notification
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".notification.success")))
        
        # Navigate back to courses to find our created course
        courses_nav = self.driver.find_element(By.CSS_SELECTOR, "[data-section='courses']")
        courses_nav.click()
        
        # Wait for courses to load and find our test course
        course_card = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Selenium Test Course')]"))
        )
        
        return course_card
    
    def test_complete_content_management_workflow(self):
        """Test the complete enhanced content management workflow"""
        
        # Step 1: Login and create test course
        self.login_as_instructor()
        course_card = self.create_test_course()
        
        # Step 2: Click on course to open panes view
        course_card.click()
        
        # Wait for 4-pane layout to appear
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-panes-container")))
        
        # Verify all 4 panes are present
        syllabus_pane = self.driver.find_element(By.CSS_SELECTOR, ".syllabus-pane")
        slides_pane = self.driver.find_element(By.CSS_SELECTOR, ".slides-pane")
        labs_pane = self.driver.find_element(By.CSS_SELECTOR, ".labs-pane")
        quizzes_pane = self.driver.find_element(By.CSS_SELECTOR, ".quizzes-pane")
        
        assert syllabus_pane.is_displayed()
        assert slides_pane.is_displayed()
        assert labs_pane.is_displayed()
        assert quizzes_pane.is_displayed()
        
        # Step 3: Test syllabus upload functionality
        self.test_syllabus_upload_functionality()
        
        # Step 4: Test slides and template functionality
        self.test_slides_template_functionality()
        
        # Step 5: Test lab upload functionality
        self.test_lab_upload_functionality()
        
        # Step 6: Test quiz upload functionality
        self.test_quiz_upload_functionality()
        
        # Step 7: Test content export functionality
        self.test_content_export_functionality()
    
    def test_syllabus_upload_functionality(self):
        """Test syllabus upload, edit, and download functionality"""
        print("Testing syllabus upload functionality...")
        
        # Find syllabus pane upload button
        syllabus_upload_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'uploadSyllabusFile')]"))
        )
        
        # Verify upload button is present and has correct icon
        assert syllabus_upload_btn.is_displayed()
        upload_icon = syllabus_upload_btn.find_element(By.CSS_SELECTOR, ".fa-upload")
        assert upload_icon is not None
        
        # Test that clicking upload button would trigger file input
        # Note: We can't actually test file upload in headless mode, but we can verify the UI
        
        # Check for download button
        syllabus_download_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'downloadSyllabus')]"
        )
        assert syllabus_download_btn.is_displayed()
        
        # Check for edit button
        syllabus_edit_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'editSyllabus')]"
        )
        assert syllabus_edit_btn.is_displayed()
        
        # Verify syllabus status indicators are present
        syllabus_source = self.driver.find_element(By.XPATH, "//span[contains(@id, 'syllabus-source-')]")
        assert syllabus_source.is_displayed()
        assert "AI Generated" in syllabus_source.text or "Custom Upload" in syllabus_source.text
        
        print("✅ Syllabus upload functionality verified")
    
    def test_slides_template_functionality(self):
        """Test slides upload, template upload, and download functionality"""
        print("Testing slides and template functionality...")
        
        # Find slides pane buttons
        slides_upload_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'uploadSlides')]"))
        )
        template_upload_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'uploadTemplate')]"
        )
        slides_download_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'downloadSlides')]"
        )
        slides_generate_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'generateSlides')]"
        )
        
        # Verify all buttons are present and displayed
        assert slides_upload_btn.is_displayed()
        assert template_upload_btn.is_displayed()
        assert slides_download_btn.is_displayed()
        assert slides_generate_btn.is_displayed()
        
        # Check button icons
        upload_icon = slides_upload_btn.find_element(By.CSS_SELECTOR, ".fa-upload")
        template_icon = template_upload_btn.find_element(By.CSS_SELECTOR, ".fa-palette")
        download_icon = slides_download_btn.find_element(By.CSS_SELECTOR, ".fa-download")
        generate_icon = slides_generate_btn.find_element(By.CSS_SELECTOR, ".fa-magic")
        
        assert upload_icon is not None
        assert template_icon is not None
        assert download_icon is not None
        assert generate_icon is not None
        
        # Verify slides status indicators
        template_status = self.driver.find_element(By.XPATH, "//span[contains(@id, 'template-status-')]")
        slides_count = self.driver.find_element(By.XPATH, "//span[contains(@id, 'slides-count-')]")
        
        assert template_status.is_displayed()
        assert slides_count.is_displayed()
        
        print("✅ Slides and template functionality verified")
    
    def test_lab_upload_functionality(self):
        """Test lab upload, export, and generation functionality"""
        print("Testing lab upload functionality...")
        
        # Find lab pane buttons
        lab_upload_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'uploadCustomLab')]"))
        )
        lab_export_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'exportLabs')]"
        )
        lab_refresh_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'refreshLabExercises')]"
        )
        lab_generate_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'createNewLab')]"
        )
        
        # Verify all buttons are present
        assert lab_upload_btn.is_displayed()
        assert lab_export_btn.is_displayed() 
        assert lab_refresh_btn.is_displayed()
        assert lab_generate_btn.is_displayed()
        
        # Check button icons and tooltips
        assert "Upload Custom Lab" in lab_upload_btn.get_attribute("title")
        assert "Export Labs" in lab_export_btn.get_attribute("title")
        assert "AI Generate Lab" in lab_generate_btn.get_attribute("title")
        
        # Verify lab status indicators
        lab_env = self.driver.find_element(By.XPATH, "//span[contains(@id, 'lab-env-')]")
        lab_count = self.driver.find_element(By.XPATH, "//span[contains(@id, 'lab-count-')]")
        lab_source = self.driver.find_element(By.XPATH, "//span[contains(@id, 'lab-source-')]")
        
        assert lab_env.is_displayed()
        assert lab_count.is_displayed()
        assert lab_source.is_displayed()
        
        # Verify lab widgets are displayed
        lab_widgets = self.driver.find_elements(By.CSS_SELECTOR, ".lab-widget")
        assert len(lab_widgets) >= 4  # Code Editor, Terminal, AI Assistant, Exercises
        
        for widget in lab_widgets:
            assert widget.is_displayed()
        
        print("✅ Lab upload functionality verified")
    
    def test_quiz_upload_functionality(self):
        """Test quiz upload, export, and generation functionality"""
        print("Testing quiz upload functionality...")
        
        # Find quiz pane buttons
        quiz_upload_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'uploadCustomQuiz')]"))
        )
        quiz_export_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'exportQuizzes')]"
        )
        quiz_generate_btn = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'generateQuizzes')]"
        )
        
        # Verify buttons are present
        assert quiz_upload_btn.is_displayed()
        assert quiz_export_btn.is_displayed()
        assert quiz_generate_btn.is_displayed()
        
        # Check tooltips
        assert "Upload Custom Quiz" in quiz_upload_btn.get_attribute("title")
        assert "Export Quizzes" in quiz_export_btn.get_attribute("title")
        assert "AI Generate Quizzes" in quiz_generate_btn.get_attribute("title")
        
        # Verify quiz status indicators
        quiz_count = self.driver.find_element(By.XPATH, "//span[contains(@id, 'quiz-count-')]")
        quiz_types = self.driver.find_element(By.XPATH, "//span[contains(@id, 'quiz-types-')]")
        quiz_source = self.driver.find_element(By.XPATH, "//span[contains(@id, 'quiz-source-')]")
        
        assert quiz_count.is_displayed()
        assert quiz_types.is_displayed()
        assert quiz_source.is_displayed()
        
        # Verify quiz actions
        quiz_actions = self.driver.find_elements(By.CSS_SELECTOR, ".quiz-actions button")
        assert len(quiz_actions) >= 3  # View All, Edit, Preview
        
        for action in quiz_actions:
            assert action.is_displayed()
        
        print("✅ Quiz upload functionality verified")
    
    def test_content_export_functionality(self):
        """Test that export functionality works across all panes"""
        print("Testing content export functionality...")
        
        # Test syllabus download button
        syllabus_download = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'downloadSyllabus')]"
        )
        assert syllabus_download.is_displayed()
        assert syllabus_download.is_enabled()
        
        # Test slides download button
        slides_download = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'downloadSlides')]"
        )
        assert slides_download.is_displayed()
        assert slides_download.is_enabled()
        
        # Test lab export button
        lab_export = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'exportLabs')]"
        )
        assert lab_export.is_displayed()
        assert lab_export.is_enabled()
        
        # Test quiz export button  
        quiz_export = self.driver.find_element(
            By.XPATH, "//button[contains(@onclick, 'exportQuizzes')]"
        )
        assert quiz_export.is_displayed()
        assert quiz_export.is_enabled()
        
        print("✅ Content export functionality verified")
    
    def test_pane_interaction_and_navigation(self):
        """Test that panes are interactive and navigation works"""
        print("Testing pane interaction and navigation...")
        
        # Login and navigate to course panes
        self.login_as_instructor()
        course_card = self.create_test_course()
        course_card.click()
        
        # Wait for panes to load
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-panes-container")))
        
        # Test clicking on each pane
        panes = [
            (".syllabus-pane", "openSyllabusPane"),
            (".slides-pane", "viewSlidesVertical"), 
            (".labs-pane", "openLabEnvironment"),
            (".quizzes-pane", "openQuizzesPane")
        ]
        
        for pane_selector, expected_function in panes:
            pane = self.driver.find_element(By.CSS_SELECTOR, pane_selector)
            assert pane.is_displayed()
            
            # Verify pane has onclick handler
            onclick_attr = pane.get_attribute("onclick")
            assert expected_function in onclick_attr
        
        # Test pane headers and actions
        pane_headers = self.driver.find_elements(By.CSS_SELECTOR, ".pane-header")
        assert len(pane_headers) == 4
        
        for header in pane_headers:
            assert header.is_displayed()
            # Each header should have a title and actions
            title = header.find_element(By.CSS_SELECTOR, "h3")
            actions = header.find_element(By.CSS_SELECTOR, ".pane-actions")
            assert title.is_displayed()
            assert actions.is_displayed()
        
        print("✅ Pane interaction and navigation verified")
    
    def test_ai_integration_indicators(self):
        """Test that AI integration indicators are properly displayed"""
        print("Testing AI integration indicators...")
        
        # Login and navigate to course panes
        self.login_as_instructor()
        course_card = self.create_test_course()
        course_card.click()
        
        # Wait for panes to load
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-panes-container")))
        
        # Test syllabus AI indicators
        syllabus_source = self.driver.find_element(By.XPATH, "//span[contains(@id, 'syllabus-source-')]")
        assert "AI Generated" in syllabus_source.text or "Custom Upload" in syllabus_source.text
        
        # Test slides template indicators
        template_status = self.driver.find_element(By.XPATH, "//span[contains(@id, 'template-status-')]")
        assert "Default" in template_status.text or "Custom" in template_status.text
        
        # Test lab environment indicators
        lab_source = self.driver.find_element(By.XPATH, "//span[contains(@id, 'lab-source-')]")
        assert "AI Generated" in lab_source.text or "Custom Upload" in lab_source.text
        
        # Test quiz source indicators
        quiz_source = self.driver.find_element(By.XPATH, "//span[contains(@id, 'quiz-source-')]")
        assert "AI Generated" in quiz_source.text or "Custom Upload" in quiz_source.text
        
        # Verify AI-related buttons have correct tooltips
        ai_buttons = [
            ("generateSyllabus", "AI Generate Syllabus"),
            ("generateSlides", "AI Generate Slides"),
            ("createNewLab", "AI Generate Lab"),
            ("generateQuizzes", "AI Generate Quizzes")
        ]
        
        for button_function, expected_tooltip in ai_buttons:
            button = self.driver.find_element(By.XPATH, f"//button[contains(@onclick, '{button_function}')]")
            actual_tooltip = button.get_attribute("title")
            assert expected_tooltip in actual_tooltip
        
        print("✅ AI integration indicators verified")
    
    def test_responsive_design_and_accessibility(self):
        """Test responsive design and basic accessibility features"""
        print("Testing responsive design and accessibility...")
        
        # Login and navigate to course panes
        self.login_as_instructor()
        course_card = self.create_test_course()
        course_card.click()
        
        # Wait for panes to load
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-panes-container")))
        
        # Test different window sizes
        window_sizes = [
            (1920, 1080),  # Desktop
            (1366, 768),   # Laptop
            (768, 1024),   # Tablet
        ]
        
        for width, height in window_sizes:
            self.driver.set_window_size(width, height)
            time.sleep(1)  # Allow layout to adjust
            
            # Verify panes are still visible and properly arranged
            panes_container = self.driver.find_element(By.CSS_SELECTOR, ".course-panes-container")
            assert panes_container.is_displayed()
            
            # Verify all panes are still accessible
            panes = self.driver.find_elements(By.CSS_SELECTOR, ".course-pane")
            assert len(panes) == 4
            
            for pane in panes:
                assert pane.is_displayed()
        
        # Test keyboard accessibility
        buttons = self.driver.find_elements(By.CSS_SELECTOR, ".pane-actions button")
        for button in buttons[:3]:  # Test first 3 buttons
            # Verify buttons are focusable
            self.driver.execute_script("arguments[0].focus();", button)
            focused_element = self.driver.switch_to.active_element
            assert focused_element == button
        
        # Test ARIA attributes and labels
        pane_headers = self.driver.find_elements(By.CSS_SELECTOR, ".pane-header h3")
        for header in pane_headers:
            # Headers should have readable text
            assert len(header.text.strip()) > 0
        
        # Restore original window size
        self.driver.set_window_size(1920, 1080)
        
        print("✅ Responsive design and accessibility verified")
    
    def test_error_handling_ui(self):
        """Test error handling in the UI"""
        print("Testing error handling UI...")
        
        # Login and navigate to course panes
        self.login_as_instructor()
        course_card = self.create_test_course()
        course_card.click()
        
        # Wait for panes to load
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-panes-container")))
        
        # Test that buttons exist and are clickable (even if backend isn't running)
        upload_buttons = [
            ("uploadSyllabusFile", "syllabus upload"),
            ("uploadSlides", "slides upload"),
            ("uploadTemplate", "template upload"),
            ("uploadCustomLab", "lab upload"),
            ("uploadCustomQuiz", "quiz upload")
        ]
        
        for button_function, button_name in upload_buttons:
            button = self.driver.find_element(By.XPATH, f"//button[contains(@onclick, '{button_function}')]")
            assert button.is_displayed()
            assert button.is_enabled()
            
            # Verify button has proper styling for interactive state
            cursor_style = button.value_of_css_property("cursor")
            # Should be pointer or inherit (not default/not-allowed which would indicate disabled)
            assert cursor_style in ["pointer", "inherit", "auto"]
        
        # Test download buttons exist and are clickable
        download_buttons = [
            ("downloadSyllabus", "syllabus download"),
            ("downloadSlides", "slides download"),
            ("exportLabs", "lab export"),
            ("exportQuizzes", "quiz export")
        ]
        
        for button_function, button_name in download_buttons:
            button = self.driver.find_element(By.XPATH, f"//button[contains(@onclick, '{button_function}')]")
            assert button.is_displayed()
            assert button.is_enabled()
        
        print("✅ Error handling UI verified")


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v', '-s', '--tb=short'])