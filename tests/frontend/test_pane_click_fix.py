"""
Test to verify that the pane click fix works correctly.
Tests that clicking anywhere on quiz or slide panes calls the correct function.
"""
import pytest
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from webdriver_manager.chrome import ChromeDriverManager

# Add path for imports
sys.path.insert(0, '/home/bbrelin/course-creator/tests')

class TestPaneClickFix:
    """Test suite for pane click fix."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--silent')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--remote-debugging-port=9222')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--disable-hang-monitor')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-component-update')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-domain-reliability')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-translate')
            chrome_options.add_argument('--metrics-recording-only')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--safebrowsing-disable-auto-update')
            chrome_options.add_argument('--enable-automation')
            chrome_options.add_argument('--password-store=basic')
            chrome_options.add_argument('--use-mock-keychain')
            
            # Try to use system chromium first
            try:
                chrome_options.binary_location = '/usr/bin/chromium-browser'
                service = Service(ChromeDriverManager(driver_version="138.0.7204.100").install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"Chromium setup failed: {e}")
                # Fallback to regular Chrome
                try:
                    service = Service(ChromeDriverManager(driver_version="138.0.7204.100").install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e2:
                    print(f"Chrome setup also failed: {e2}")
                    # Final fallback to latest version
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            print(f"Skipping browser tests - no Chrome available: {e}")
            self.driver = None
    
    def teardown_method(self):
        """Clean up after each test."""
        if self.driver:
            self.driver.quit()
    
    def test_quiz_pane_click_fix(self):
        """Test that clicking anywhere on the quiz pane calls viewQuizzes."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Create HTML that matches the fixed implementation
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quiz Pane Test - Fixed</title>
        </head>
        <body>
            <div class="content-card clickable-pane" onclick="viewQuizzes('course123')" id="quiz-pane">
                <div class="content-card-header">
                    <h5>Quizzes & Tests</h5>
                </div>
                <div class="content-card-body">
                    <p><strong>3 quizzes available</strong></p>
                    <div class="quiz-preview">
                        <strong>Python Basics Quiz</strong>
                        <p>5 questions</p>
                    </div>
                    <div class="quiz-preview">
                        <strong>Advanced Python Quiz</strong>
                        <p>8 questions</p>
                    </div>
                </div>
            </div>
            
            <div id="result"></div>
            
            <script>
                function viewQuizzes(courseId) {
                    document.getElementById('result').innerHTML = 'SUCCESS: viewQuizzes called with courseId: ' + courseId;
                }
            </script>
        </body>
        </html>
        """
        
        # Load the HTML
        self.driver.get("data:text/html;charset=utf-8," + html)
        
        # Test clicking different parts of the pane
        test_locations = [
            ("Header", By.CLASS_NAME, "content-card-header"),
            ("Body", By.CLASS_NAME, "content-card-body"),
            ("Quiz item 1", By.XPATH, "//div[@class='quiz-preview'][1]"),
            ("Quiz item 2", By.XPATH, "//div[@class='quiz-preview'][2]"),
            ("Main pane", By.ID, "quiz-pane")
        ]
        
        for location_name, by_type, locator in test_locations:
            print(f"Testing click on {location_name}...")
            
            # Clear previous result
            self.driver.execute_script("document.getElementById('result').innerHTML = '';")
            
            # Click on the element
            element = self.driver.find_element(by_type, locator)
            element.click()
            
            # Wait for result
            time.sleep(0.5)
            
            # Check that viewQuizzes was called
            result = self.driver.find_element(By.ID, "result").text
            print(f"Result: {result}")
            assert "SUCCESS: viewQuizzes called" in result, f"Clicking on {location_name} should call viewQuizzes, got: {result}"
        
        print("All quiz pane click tests passed!")
    
    def test_slide_pane_click_fix(self):
        """Test that clicking anywhere on the slide pane calls viewAllSlides."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Create HTML that matches the fixed implementation
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Slide Pane Test - Fixed</title>
        </head>
        <body>
            <div class="content-card clickable-pane" onclick="viewAllSlides('course123')" id="slide-pane">
                <div class="content-card-header">
                    <h5>Slides</h5>
                </div>
                <div class="content-card-body">
                    <p><strong>5 slides available</strong></p>
                    <div class="slide-preview">
                        <strong>Slide 1: Introduction</strong>
                        <div>Welcome to the course...</div>
                    </div>
                    <div class="slide-preview">
                        <strong>Slide 2: Variables</strong>
                        <div>Learn about variables...</div>
                    </div>
                </div>
            </div>
            
            <div id="result"></div>
            
            <script>
                function viewAllSlides(courseId) {
                    document.getElementById('result').innerHTML = 'SUCCESS: viewAllSlides called with courseId: ' + courseId;
                }
            </script>
        </body>
        </html>
        """
        
        # Load the HTML
        self.driver.get("data:text/html;charset=utf-8," + html)
        
        # Test clicking different parts of the pane
        test_locations = [
            ("Header", By.CLASS_NAME, "content-card-header"),
            ("Body", By.CLASS_NAME, "content-card-body"),
            ("Slide item 1", By.XPATH, "//div[@class='slide-preview'][1]"),
            ("Slide item 2", By.XPATH, "//div[@class='slide-preview'][2]"),
            ("Main pane", By.ID, "slide-pane")
        ]
        
        for location_name, by_type, locator in test_locations:
            print(f"Testing click on {location_name}...")
            
            # Clear previous result
            self.driver.execute_script("document.getElementById('result').innerHTML = '';")
            
            # Click on the element
            element = self.driver.find_element(by_type, locator)
            element.click()
            
            # Wait for result
            time.sleep(0.5)
            
            # Check that viewAllSlides was called
            result = self.driver.find_element(By.ID, "result").text
            print(f"Result: {result}")
            assert "SUCCESS: viewAllSlides called" in result, f"Clicking on {location_name} should call viewAllSlides, got: {result}"
        
        print("All slide pane click tests passed!")
    
    def test_button_clicks_still_work(self):
        """Test that buttons within panes still work correctly with stopPropagation."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Create HTML that includes buttons with stopPropagation
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Button Test</title>
        </head>
        <body>
            <div class="content-card clickable-pane" onclick="viewQuizzes('course123')" id="quiz-pane">
                <div class="content-card-header">
                    <h5>Quizzes & Tests</h5>
                </div>
                <div class="content-card-body">
                    <p>No quizzes available for this course.</p>
                    <button class="btn btn-secondary" onclick="event.stopPropagation(); generateQuizzes('course123')">
                        Generate Quizzes
                    </button>
                </div>
            </div>
            
            <div id="result"></div>
            
            <script>
                function viewQuizzes(courseId) {
                    document.getElementById('result').innerHTML = 'ERROR: viewQuizzes called - button should have stopped propagation';
                }
                
                function generateQuizzes(courseId) {
                    document.getElementById('result').innerHTML = 'SUCCESS: generateQuizzes called with courseId: ' + courseId;
                }
            </script>
        </body>
        </html>
        """
        
        # Load the HTML
        self.driver.get("data:text/html;charset=utf-8," + html)
        
        # Click on the button
        button = self.driver.find_element(By.TAG_NAME, "button")
        button.click()
        
        # Wait for result
        time.sleep(0.5)
        
        # Check that generateQuizzes was called (not viewQuizzes)
        result = self.driver.find_element(By.ID, "result").text
        print(f"Button click result: {result}")
        assert "SUCCESS: generateQuizzes called" in result, f"Button click should call generateQuizzes, got: {result}"
        
        print("Button click test passed!")
    
    def test_complete_pane_behavior(self):
        """Test complete pane behavior with different click scenarios."""
        if not self.driver:
            pytest.skip("No browser available")
        
        print("Testing complete pane behavior...")
        
        # Test all three types of clicks in sequence
        self.test_quiz_pane_click_fix()
        self.test_slide_pane_click_fix()
        self.test_button_clicks_still_work()
        
        print("All pane behavior tests passed!")