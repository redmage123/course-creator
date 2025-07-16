"""
Core JavaScript functionality tests using Selenium.
These tests would have caught the JavaScript errors we recently fixed.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@pytest.mark.javascript
@pytest.mark.smoke
class TestJavaScriptCore:
    """Test core JavaScript functionality."""
    
    def test_page_loads_without_javascript_errors(self, driver, javascript_utils, frontend_server):
        """Test that all pages load without JavaScript errors."""
        pages = [
            f"{frontend_server}/index.html",
            f"{frontend_server}/instructor-dashboard.html", 
            f"{frontend_server}/student-dashboard.html",
            f"{frontend_server}/admin.html",
            f"{frontend_server}/lab.html"
        ]
        
        for page_url in pages:
            driver.get(page_url)
            javascript_utils.wait_for_page_load()
            
            # Check for JavaScript errors
            errors = javascript_utils.get_console_errors()
            assert len(errors) == 0, f"JavaScript errors found on {page_url}: {errors}"
            
            # Check for module loading errors
            module_errors = javascript_utils.get_module_errors()
            assert len(module_errors) == 0, f"Module loading errors on {page_url}: {module_errors}"
    
    def test_es6_modules_load_correctly(self, driver, javascript_utils, frontend_server):
        """Test that ES6 modules load without errors."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Wait for modules to load
        javascript_utils.wait_for_function("App", timeout=15)
        
        # Check that main modules are available
        assert javascript_utils.function_exists("App"), "App module not loaded"
        assert driver.execute_script("return typeof window.Auth !== 'undefined'"), "Auth module not loaded"
        assert driver.execute_script("return typeof window.Navigation !== 'undefined'"), "Navigation module not loaded"
        assert driver.execute_script("return typeof window.showNotification !== 'undefined'"), "Notification module not loaded"
    
    def test_no_duplicate_exports(self, driver, javascript_utils, frontend_server):
        """Test that there are no duplicate export errors (issue we fixed)."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Check console for duplicate export errors
        errors = javascript_utils.get_console_errors()
        duplicate_errors = [e for e in errors if 'Duplicate export' in e['message']]
        
        assert len(duplicate_errors) == 0, f"Duplicate export errors found: {duplicate_errors}"
    
    def test_all_required_functions_available(self, driver, javascript_utils, frontend_server):
        """Test that all required functions are available (issue we fixed)."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Wait for main-modular.js to load
        javascript_utils.wait_for_function("showLoginModal", timeout=15)
        
        required_functions = [
            'showLoginModal',
            'showRegisterModal', 
            'loadCourses',
            'logout',
            'toggleAccountDropdown',
            'authenticatedFetch',
            'showNotification',
            'showErrorLogs',
            'trackActivity'
        ]
        
        for func_name in required_functions:
            assert javascript_utils.function_exists(func_name), f"Function {func_name} is not available"
            assert javascript_utils.get_function_type(func_name) == 'function', f"{func_name} is not a function"
    
    def test_config_object_available(self, driver, javascript_utils, frontend_server):
        """Test that CONFIG object is properly available."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Check CONFIG is available
        config_available = driver.execute_script("return typeof window.CONFIG !== 'undefined'")
        assert config_available, "CONFIG object not available"
        
        # Check CONFIG has required properties
        has_api_urls = driver.execute_script("return window.CONFIG && typeof window.CONFIG.API_URLS !== 'undefined'")
        assert has_api_urls, "CONFIG.API_URLS not available"
        
        has_endpoints = driver.execute_script("return window.CONFIG && typeof window.CONFIG.ENDPOINTS !== 'undefined'")
        assert has_endpoints, "CONFIG.ENDPOINTS not available"


@pytest.mark.javascript
@pytest.mark.smoke
class TestFunctionCalls:
    """Test that functions can be called without errors."""
    
    def test_show_login_modal_callable(self, driver, javascript_utils, frontend_server):
        """Test that showLoginModal can be called without errors."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("showLoginModal")
        
        # Clear any existing errors
        javascript_utils.clear_console()
        
        # Call the function
        driver.execute_script("window.showLoginModal()")
        
        # Check for errors after calling
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"Errors occurred when calling showLoginModal: {errors}"
    
    def test_load_courses_callable(self, driver, javascript_utils, frontend_server):
        """Test that loadCourses can be called without errors (issue we fixed)."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("loadCourses")
        
        # Clear any existing errors
        javascript_utils.clear_console()
        
        # Call the function
        driver.execute_script("window.loadCourses()")
        
        # Check for errors after calling
        errors = javascript_utils.get_console_errors()
        reference_errors = [e for e in errors if 'loadCourses is not defined' in e['message']]
        
        assert len(reference_errors) == 0, f"loadCourses reference errors: {reference_errors}"
    
    def test_logout_callable(self, driver, javascript_utils, frontend_server):
        """Test that logout function can be called."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("logout")
        
        # Clear any existing errors
        javascript_utils.clear_console()
        
        # Call the function (it should redirect, so we'll check it exists and is callable)
        try:
            driver.execute_script("window.logout()")
            # If we get here without error, the function executed
        except Exception as e:
            # If there's a redirect or navigation, that's expected
            if "navigation" not in str(e).lower():
                pytest.fail(f"logout() function failed: {e}")
    
    def test_toggle_account_dropdown_callable(self, driver, javascript_utils, frontend_server):
        """Test that toggleAccountDropdown can be called."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("toggleAccountDropdown")
        
        # Clear any existing errors
        javascript_utils.clear_console()
        
        # Call the function
        driver.execute_script("window.toggleAccountDropdown()")
        
        # Check for errors after calling
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"Errors occurred when calling toggleAccountDropdown: {errors}"


@pytest.mark.javascript
@pytest.mark.smoke
class TestButtonClicks:
    """Test that button clicks work without JavaScript errors."""
    
    def test_login_button_click(self, driver, javascript_utils, page_objects, frontend_server):
        """Test that login button click works without errors."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("showLoginModal")
        
        # Clear any existing errors
        javascript_utils.clear_console()
        
        # Click login button
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Check for errors after click
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"Errors occurred when clicking login button: {errors}"
    
    def test_register_button_click(self, driver, javascript_utils, page_objects, frontend_server):
        """Test that register button click works without errors."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("showRegisterModal")
        
        # Clear any existing errors
        javascript_utils.clear_console()
        
        # Click register button
        register_button = page_objects.get_register_button()
        register_button.click()
        
        # Check for errors after click
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"Errors occurred when clicking register button: {errors}"
    
    def test_view_courses_button_click(self, driver, javascript_utils, page_objects, frontend_server):
        """Test that View Courses button click works without errors (issue we fixed)."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("loadCourses")
        
        # Clear any existing errors
        javascript_utils.clear_console()
        
        # Click view courses button
        courses_button = page_objects.get_courses_button()
        courses_button.click()
        
        # Check for errors after click
        errors = javascript_utils.get_console_errors()
        reference_errors = [e for e in errors if 'loadCourses is not defined' in e['message']]
        
        assert len(reference_errors) == 0, f"loadCourses reference errors after button click: {reference_errors}"


@pytest.mark.javascript
@pytest.mark.regression
class TestModularSystemMigration:
    """Test that the modular system migration was successful."""
    
    def test_legacy_main_js_removed(self, driver, frontend_server):
        """Test that legacy main.js is no longer referenced."""
        driver.get(f"{frontend_server}/index.html")
        
        # Check that main.js is not in the page source
        page_source = driver.page_source
        assert 'main.js' not in page_source, "Legacy main.js still referenced in HTML"
    
    def test_only_modular_system_loaded(self, driver, javascript_utils, frontend_server):
        """Test that only the modular system is loaded."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Check that main-modular.js loaded successfully
        javascript_utils.wait_for_function("App", timeout=15)
        
        # Verify modular system components are loaded
        assert driver.execute_script("return typeof window.App !== 'undefined'"), "App module not loaded"
        assert driver.execute_script("return typeof window.Auth !== 'undefined'"), "Auth module not loaded"
        assert driver.execute_script("return typeof window.Navigation !== 'undefined'"), "Navigation module not loaded"
        
        # Check for successful load message
        logs = driver.get_log('browser')
        success_logs = [log for log in logs if 'Course Creator Platform (Modular) loaded successfully' in log['message']]
        assert len(success_logs) > 0, "Modular system success message not found"
    
    def test_no_legacy_references(self, driver, javascript_utils, frontend_server):
        """Test that there are no references to legacy system."""
        pages = [
            f"{frontend_server}/index.html",
            f"{frontend_server}/instructor-dashboard.html",
            f"{frontend_server}/student-dashboard.html"
        ]
        
        for page_url in pages:
            driver.get(page_url)
            javascript_utils.wait_for_page_load()
            
            # Check page source for legacy references
            page_source = driver.page_source
            assert 'nomodule' not in page_source, f"Legacy nomodule script found in {page_url}"
            assert 'main.js' not in page_source, f"Legacy main.js reference found in {page_url}"
    
    def test_all_pages_use_modular_system(self, driver, javascript_utils, frontend_server):
        """Test that all pages use the modular system."""
        pages = [
            f"{frontend_server}/index.html",
            f"{frontend_server}/instructor-dashboard.html",
            f"{frontend_server}/student-dashboard.html"
        ]
        
        for page_url in pages:
            driver.get(page_url)
            javascript_utils.wait_for_page_load()
            
            # Check that modular system is loaded
            page_source = driver.page_source
            assert 'main-modular.js' in page_source, f"Modular system not loaded in {page_url}"
            assert 'type="module"' in page_source, f"ES6 module type not found in {page_url}"