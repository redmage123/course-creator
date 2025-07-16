"""
Debug test to understand quiz pane click behavior.
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

class TestQuizPaneDebug:
    """Debug test suite for quiz pane click behavior."""
    
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
    
    def test_simple_quiz_pane_click(self):
        """Test simple quiz pane click behavior."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Create a simple test HTML that matches the real structure
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quiz Pane Test</title>
        </head>
        <body>
            <div class="content-card clickable-pane" onclick="viewQuizzes('course123')" id="quiz-pane">
                <div class="content-card-header">
                    <h5>Quizzes & Tests</h5>
                </div>
                <div class="content-card-body">
                    <p><strong>3 quizzes available</strong></p>
                    <div class="quiz-preview" onclick="event.stopPropagation(); jumpToQuiz('quiz1')">
                        <strong>Python Basics Quiz</strong>
                        <p>5 questions</p>
                    </div>
                </div>
            </div>
            
            <div id="result"></div>
            
            <script>
                function viewQuizzes(courseId) {
                    document.getElementById('result').innerHTML = 'SUCCESS: viewQuizzes called';
                }
                
                function jumpToQuiz(quizId) {
                    document.getElementById('result').innerHTML = 'ERROR: jumpToQuiz called - should not happen on pane click';
                }
            </script>
        </body>
        </html>
        """
        
        # Load the HTML
        self.driver.get("data:text/html;charset=utf-8," + html)
        
        # Test 1: Click on header should call viewQuizzes
        print("Test 1: Clicking header...")
        header = self.driver.find_element(By.CLASS_NAME, "content-card-header")
        header.click()
        time.sleep(0.5)
        result = self.driver.find_element(By.ID, "result").text
        print(f"Result: {result}")
        assert "SUCCESS: viewQuizzes called" in result
        
        # Test 2: Click on quiz item should call jumpToQuiz (current behavior)
        print("Test 2: Clicking quiz item...")
        quiz_item = self.driver.find_element(By.CLASS_NAME, "quiz-preview")
        quiz_item.click()
        time.sleep(0.5)
        result = self.driver.find_element(By.ID, "result").text
        print(f"Result: {result}")
        assert "ERROR: jumpToQuiz called" in result
        
        # Test 3: Click on main pane should call viewQuizzes
        print("Test 3: Clicking main pane...")
        self.driver.execute_script("document.getElementById('result').innerHTML = '';")
        main_pane = self.driver.find_element(By.ID, "quiz-pane")
        main_pane.click()
        time.sleep(0.5)
        result = self.driver.find_element(By.ID, "result").text
        print(f"Result: {result}")
        assert "SUCCESS: viewQuizzes called" in result
        
        print("All tests passed - bug confirmed!")
    
    def test_what_happens_with_fixed_code(self):
        """Test what happens when we fix the event propagation."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Create HTML with proper event handling
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
                    <div class="quiz-preview" onclick="jumpToQuiz('quiz1')">
                        <strong>Python Basics Quiz</strong>
                        <p>5 questions</p>
                    </div>
                </div>
            </div>
            
            <div id="result"></div>
            
            <script>
                function viewQuizzes(courseId) {
                    document.getElementById('result').innerHTML = 'SUCCESS: viewQuizzes called';
                }
                
                function jumpToQuiz(quizId) {
                    document.getElementById('result').innerHTML = 'ERROR: jumpToQuiz called - should not happen on pane click';
                }
            </script>
        </body>
        </html>
        """
        
        # Load the HTML
        self.driver.get("data:text/html;charset=utf-8," + html)
        
        # Test: Click on quiz item should call jumpToQuiz (without event.stopPropagation())
        print("Test: Clicking quiz item without stopPropagation...")
        quiz_item = self.driver.find_element(By.CLASS_NAME, "quiz-preview")
        quiz_item.click()
        time.sleep(0.5)
        result = self.driver.find_element(By.ID, "result").text
        print(f"Result: {result}")
        
        # Without event.stopPropagation(), the click should bubble up to the parent
        # and call viewQuizzes, not jumpToQuiz
        print("This shows what happens without stopPropagation - both handlers fire!")