"""
Selenium test configuration and fixtures for frontend testing.
"""

import pytest
import time
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(scope="session")
def frontend_server():
    """Start frontend server for testing session."""
    print("Starting frontend server...")
    
    # Kill any existing server on port 8080
    try:
        subprocess.run(["pkill", "-f", "python.*http.server.*8080"], check=False)
        time.sleep(2)
    except:
        pass
    
    # Start server
    process = subprocess.Popen(
        ["python", "-m", "http.server", "8080"],
        cwd="/home/bbrelin/course-creator/frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    yield f"http://localhost:8080"
    
    # Cleanup
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def backend_services():
    """Ensure backend services are running."""
    # Check if services are running
    try:
        import requests
        services = [
            ("user-management", "http://localhost:8000/health"),
            ("course-generator", "http://localhost:8001/health"),
            ("content-storage", "http://localhost:8003/health"),
            ("course-management", "http://localhost:8004/health"),
            ("content-management", "http://localhost:8005/health"),
        ]
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✓ {service_name} is running")
                else:
                    print(f"⚠ {service_name} returned {response.status_code}")
            except requests.exceptions.RequestException:
                print(f"✗ {service_name} is not responding")
                
    except ImportError:
        print("⚠ requests not available, skipping service checks")
    
    yield


@pytest.fixture
def chrome_options():
    """Configure Chrome/Chromium options for testing."""
    options = Options()
    
    # Basic security and performance options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--window-size=1920,1080")
    
    # For server environments
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--safebrowsing-disable-auto-update")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--ignore-certificate-errors-spki-list")
    
    # Always run headless on server
    options.add_argument("--headless")
    
    # Enable logging
    options.add_argument("--enable-logging")
    options.add_argument("--log-level=0")
    
    # Set binary path for Chromium
    options.binary_location = "/usr/bin/chromium-browser"
    
    return options


@pytest.fixture
def driver(chrome_options, frontend_server, backend_services):
    """Create Chrome WebDriver instance."""
    try:
        # Try to use webdriver-manager with proper version matching
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        
        # Set up logging
        try:
            driver.execute_cdp_cmd("Log.enable", {})
        except Exception:
            # CDP commands might not work with all versions
            pass
        
        yield driver
        
        driver.quit()
        
    except Exception as e:
        pytest.skip(f"Chrome WebDriver setup failed: {e}. This is expected in environments without GUI support.")


@pytest.fixture
def wait(driver):
    """Create WebDriverWait instance."""
    return WebDriverWait(driver, 10)


@pytest.fixture
def javascript_utils(driver):
    """Utility functions for JavaScript testing."""
    class JavaScriptUtils:
        def __init__(self, driver):
            self.driver = driver
            
        def get_console_errors(self):
            """Get JavaScript console errors."""
            logs = self.driver.get_log('browser')
            return [log for log in logs if log['level'] == 'SEVERE']
            
        def function_exists(self, func_name):
            """Check if a function exists in window object."""
            return self.driver.execute_script(f"return typeof window.{func_name} === 'function'")
            
        def get_function_type(self, func_name):
            """Get the type of a function."""
            return self.driver.execute_script(f"return typeof window.{func_name}")
            
        def call_function(self, func_name, *args):
            """Call a JavaScript function."""
            args_str = ', '.join(f'"{arg}"' if isinstance(arg, str) else str(arg) for arg in args)
            return self.driver.execute_script(f"return window.{func_name}({args_str})")
            
        def clear_console(self):
            """Clear console logs."""
            self.driver.execute_script("console.clear()")
            
        def wait_for_function(self, func_name, timeout=10):
            """Wait for a function to be available."""
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda d: d.execute_script(f"return typeof window.{func_name} === 'function'"))
            
        def get_module_errors(self):
            """Get ES6 module loading errors."""
            logs = self.driver.get_log('browser')
            return [log for log in logs if 'Failed to load module' in log['message'] or 'SyntaxError' in log['message']]
            
        def wait_for_page_load(self):
            """Wait for page to fully load."""
            wait = WebDriverWait(self.driver, 30)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
        def get_local_storage(self, key):
            """Get localStorage value."""
            return self.driver.execute_script(f"return localStorage.getItem('{key}')")
            
        def set_local_storage(self, key, value):
            """Set localStorage value."""
            self.driver.execute_script(f"localStorage.setItem('{key}', '{value}')")
            
        def clear_local_storage(self):
            """Clear localStorage."""
            self.driver.execute_script("localStorage.clear()")
            
    return JavaScriptUtils(driver)


@pytest.fixture
def page_objects(driver, wait):
    """Page object utilities."""
    class PageObjects:
        def __init__(self, driver, wait):
            self.driver = driver
            self.wait = wait
            
        def get_login_modal(self):
            """Get login modal element."""
            return self.wait.until(EC.presence_of_element_located((By.ID, "login-modal")))
            
        def get_register_modal(self):
            """Get register modal element."""
            return self.wait.until(EC.presence_of_element_located((By.ID, "register-modal")))
            
        def get_login_button(self):
            """Get login button element."""
            return self.driver.find_element(By.CSS_SELECTOR, ".btn-login")
            
        def get_register_button(self):
            """Get register button element."""
            return self.driver.find_element(By.CSS_SELECTOR, ".btn-register")
            
        def get_courses_button(self):
            """Get view courses button element."""
            return self.driver.find_element(By.XPATH, "//button[contains(text(), 'View Courses')]")
            
        def get_account_dropdown(self):
            """Get account dropdown element."""
            return self.driver.find_element(By.ID, "accountDropdown")
            
        def get_account_menu(self):
            """Get account menu element."""
            return self.driver.find_element(By.ID, "accountMenu")
            
        def fill_login_form(self, email, password):
            """Fill login form."""
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            password_input = self.driver.find_element(By.ID, "password")
            
            email_input.clear()
            email_input.send_keys(email)
            password_input.clear()
            password_input.send_keys(password)
            
        def submit_login_form(self):
            """Submit login form."""
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "[type='submit']")
            submit_button.click()
            
        def wait_for_element_visible(self, locator, timeout=10):
            """Wait for element to be visible."""
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.visibility_of_element_located(locator))
            
        def wait_for_element_clickable(self, locator, timeout=10):
            """Wait for element to be clickable."""
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable(locator))
            
    return PageObjects(driver, wait)


@pytest.fixture
def test_data():
    """Test data for various scenarios."""
    return {
        "users": {
            "valid_user": {
                "email": "test@example.com",
                "password": "testpassword123",
                "username": "testuser"
            },
            "invalid_user": {
                "email": "invalid@example.com",
                "password": "wrongpassword"
            },
            "admin_user": {
                "email": "admin@example.com", 
                "password": "adminpass123",
                "role": "admin"
            },
            "instructor_user": {
                "email": "instructor@example.com",
                "password": "instructorpass123", 
                "role": "instructor"
            }
        },
        "courses": {
            "sample_course": {
                "title": "Test Course",
                "description": "A test course for Selenium testing",
                "category": "programming"
            }
        },
        "urls": {
            "base": "http://localhost:8080",
            "instructor_dashboard": "http://localhost:8080/instructor-dashboard.html",
            "student_dashboard": "http://localhost:8080/student-dashboard.html",
            "admin_dashboard": "http://localhost:8080/admin.html",
            "lab": "http://localhost:8080/lab.html"
        }
    }


# Test markers
pytest.mark.smoke = pytest.mark.marker("smoke")
pytest.mark.regression = pytest.mark.marker("regression")
pytest.mark.frontend = pytest.mark.marker("frontend")
pytest.mark.auth = pytest.mark.marker("auth")
pytest.mark.navigation = pytest.mark.marker("navigation")
pytest.mark.javascript = pytest.mark.marker("javascript")
pytest.mark.responsive = pytest.mark.marker("responsive")
pytest.mark.cross_browser = pytest.mark.marker("cross_browser")