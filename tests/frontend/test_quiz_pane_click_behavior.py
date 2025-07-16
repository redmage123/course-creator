"""
Test suite for quiz pane click behavior.
Tests that clicking anywhere on the quizzes pane brings user to quizzes page.
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

class TestQuizPaneClickBehavior:
    """Test suite for quiz pane click behavior."""
    
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
    
    def create_quiz_pane_html(self):
        """Create HTML with quiz pane structure that matches the actual implementation."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quiz Pane Test</title>
            <style>
                .content-card {
                    border: 1px solid #ccc;
                    margin: 10px;
                    padding: 20px;
                    width: 300px;
                    height: 200px;
                }
                
                .clickable-pane {
                    cursor: pointer;
                    transition: all 0.3s ease;
                }
                
                .clickable-pane:hover {
                    background-color: #f0f0f0;
                    transform: translateY(-2px);
                }
                
                .content-card-header {
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                
                .content-card-body {
                    font-size: 14px;
                }
                
                .quiz-preview {
                    margin: 5px 0;
                    padding: 8px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }
                
                .quiz-preview:hover {
                    background-color: #e9ecef;
                }
                
                .btn {
                    padding: 5px 10px;
                    margin: 2px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                }
                
                #result {
                    margin-top: 20px;
                    padding: 10px;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <div class="content-card clickable-pane" onclick="viewQuizzes('course123')" id="quiz-pane">
                <div class="content-card-header">
                    <h5><i class="fas fa-question-circle"></i> Quizzes & Tests</h5>
                    <div class="pane-action-hint"><i class="fas fa-mouse-pointer"></i> Click to view</div>
                </div>
                <div class="content-card-body">
                    <p><strong>3 quizzes available</strong></p>
                    <div class="quizzes-list">
                        <div class="quiz-preview clickable-quiz" onclick="event.stopPropagation(); jumpToQuiz('quiz1')">
                            <strong>Python Basics Quiz</strong>
                            <p>5 questions</p>
                            <div class="quiz-preview-actions">
                                <i class="fas fa-play"></i> Click to start
                            </div>
                        </div>
                        <div class="quiz-preview clickable-quiz" onclick="event.stopPropagation(); jumpToQuiz('quiz2')">
                            <strong>Advanced Python Quiz</strong>
                            <p>8 questions</p>
                            <div class="quiz-preview-actions">
                                <i class="fas fa-play"></i> Click to start
                            </div>
                        </div>
                        <div class="quiz-preview clickable-quiz" onclick="event.stopPropagation(); jumpToQuiz('quiz3')">
                            <strong>Data Structures Quiz</strong>
                            <p>6 questions</p>
                            <div class="quiz-preview-actions">
                                <i class="fas fa-play"></i> Click to start
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="result"></div>
            
            <script>
                let clickResults = [];
                
                function viewQuizzes(courseId) {
                    document.getElementById('result').innerHTML = 'SUCCESS: viewQuizzes called with courseId: ' + courseId;
                    clickResults.push('viewQuizzes');
                }
                
                function jumpToQuiz(quizId) {
                    document.getElementById('result').innerHTML = 'ERROR: jumpToQuiz called with quizId: ' + quizId + ' - This should not happen when clicking on pane';
                    clickResults.push('jumpToQuiz');
                }
                
                function clearResults() {
                    clickResults = [];
                    document.getElementById('result').innerHTML = '';
                }
            </script>
        </body>
        </html>
        """
    
    def test_clicking_quiz_pane_header_calls_view_quizzes(self):
        """Test that clicking on the quiz pane header calls viewQuizzes."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Load the test HTML
        self.driver.get("data:text/html;charset=utf-8," + self.create_quiz_pane_html())
        
        # Click on the header
        header = self.driver.find_element(By.CLASS_NAME, "content-card-header")
        header.click()
        
        # Wait for result
        time.sleep(0.5)
        
        # Check that viewQuizzes was called
        result = self.driver.find_element(By.ID, "result").text
        assert "SUCCESS: viewQuizzes called" in result, f"Expected viewQuizzes to be called, got: {result}"
    
    def test_clicking_quiz_item_calls_jump_to_quiz_not_view_quizzes(self):
        """Test that clicking on a quiz item calls jumpToQuiz (current broken behavior)."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Load the test HTML
        self.driver.get("data:text/html;charset=utf-8," + self.create_quiz_pane_html())
        
        # Click on a quiz item
        quiz_item = self.driver.find_element(By.XPATH, "//div[@class='quiz-preview'][1]")
        quiz_item.click()
        
        # Wait for result
        time.sleep(0.5)
        
        # Check that jumpToQuiz was called (this is the current broken behavior)
        result = self.driver.find_element(By.ID, "result").text
        assert "ERROR: jumpToQuiz called" in result, f"Expected jumpToQuiz to be called (showing current bug), got: {result}"
    
    def test_clicking_anywhere_on_quiz_pane_should_call_view_quizzes(self):
        """Test that clicking anywhere on the quiz pane should call viewQuizzes (this will fail initially)."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Load the test HTML
        self.driver.get("data:text/html;charset=utf-8," + self.create_quiz_pane_html())
        
        # Test different click locations on the pane
        test_locations = [
            (By.CLASS_NAME, "content-card-header"),  # Header
            (By.CLASS_NAME, "pane-action-hint"),     # Action hint
            (By.XPATH, "//div[@class='quiz-item'][1]"),  # First quiz item
            (By.XPATH, "//div[@class='quiz-item'][2]"),  # Second quiz item
            (By.XPATH, "//div[@class='quiz-item'][3]"),  # Third quiz item
            (By.CLASS_NAME, "content-card-body"),    # Body area
        ]
        
        for i, (by_type, locator) in enumerate(test_locations):
            # Clear previous results
            self.driver.execute_script("clearResults()")
            
            # Click on the element
            element = self.driver.find_element(by_type, locator)
            element.click()
            
            # Wait for result
            time.sleep(0.5)
            
            # Check that viewQuizzes was called
            result = self.driver.find_element(By.ID, "result").text
            location_name = locator if isinstance(locator, str) else f"location_{i}"
            
            assert "SUCCESS: viewQuizzes called" in result, f"Clicking on {location_name} should call viewQuizzes, got: {result}"
    
    def test_clicking_edit_delete_buttons_should_not_trigger_pane_click(self):
        """Test that clicking edit/delete buttons should not trigger the pane click."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Load the test HTML
        self.driver.get("data:text/html;charset=utf-8," + self.create_quiz_pane_html())
        
        # Click on edit button
        edit_button = self.driver.find_element(By.XPATH, "//button[text()='Edit']")
        edit_button.click()
        
        # Wait for result
        time.sleep(0.5)
        
        # Check that editQuiz was called (and not viewQuizzes)
        result = self.driver.find_element(By.ID, "result").text
        assert "ERROR: editQuiz called" in result, f"Expected editQuiz to be called, got: {result}"
        
        # Clear results
        self.driver.execute_script("clearResults()")
        
        # Click on delete button
        delete_button = self.driver.find_element(By.XPATH, "//button[text()='Delete']")
        delete_button.click()
        
        # Wait for result
        time.sleep(0.5)
        
        # Check that deleteQuiz was called (and not viewQuizzes)
        result = self.driver.find_element(By.ID, "result").text
        assert "ERROR: deleteQuiz called" in result, f"Expected deleteQuiz to be called, got: {result}"
    
    def test_event_propagation_behavior(self):
        """Test event propagation behavior to understand the current implementation."""
        if not self.driver:
            pytest.skip("No browser available")
        
        # Load the test HTML
        self.driver.get("data:text/html;charset=utf-8," + self.create_quiz_pane_html())
        
        # Test clicking on different elements to see which events fire
        test_elements = [
            ("pane", By.ID, "quiz-pane"),
            ("header", By.CLASS_NAME, "content-card-header"),
            ("quiz-item", By.XPATH, "//div[@class='quiz-item'][1]"),
            ("button", By.XPATH, "//button[text()='Edit']"),
        ]
        
        results = {}
        
        for name, by_type, locator in test_elements:
            # Clear previous results
            self.driver.execute_script("clearResults()")
            
            # Click on the element
            element = self.driver.find_element(by_type, locator)
            element.click()
            
            # Wait for result
            time.sleep(0.5)
            
            # Get the result
            result = self.driver.find_element(By.ID, "result").text
            results[name] = result
        
        # Print results for debugging
        print("Event propagation test results:")
        for name, result in results.items():
            print(f"  {name}: {result}")
        
        # The main pane should always call viewQuizzes
        assert "SUCCESS: viewQuizzes called" in results["pane"], "Main pane should call viewQuizzes"
        
        # Header should call viewQuizzes
        assert "SUCCESS: viewQuizzes called" in results["header"], "Header should call viewQuizzes"
        
        # Quiz items should call viewQuizzes (this is what we want to fix)
        # This assertion will fail initially, showing the bug
        assert "SUCCESS: viewQuizzes called" in results["quiz-item"], "Quiz items should call viewQuizzes, not takeQuiz"
        
        # Buttons should call their specific functions
        assert "ERROR: editQuiz called" in results["button"], "Edit button should call editQuiz"