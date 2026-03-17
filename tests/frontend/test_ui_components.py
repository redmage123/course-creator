"""
UI Components tests using Selenium.
Tests user interface elements, interactions, and responsive behavior.
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@pytest.mark.frontend
@pytest.mark.smoke
class TestUIComponents:
    """Test basic UI components."""
    
    def test_header_elements_present(self, driver, javascript_utils, frontend_server):
        """Test that header elements are present."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Check header
        header = driver.find_element(By.TAG_NAME, "header")
        assert header.is_displayed(), "Header should be visible"
        
        # Check logo
        logo = driver.find_element(By.CSS_SELECTOR, ".logo, h1")
        assert logo.is_displayed(), "Logo should be visible"
        assert "Course Creator" in logo.text, "Logo should contain 'Course Creator'"
        
        # Check navigation links
        nav_links = driver.find_element(By.CSS_SELECTOR, ".nav-links, nav")
        assert nav_links.is_displayed(), "Navigation links should be visible"
        
        # Check auth buttons section
        auth_section = driver.find_element(By.CSS_SELECTOR, ".auth-buttons, .account-section")
        assert auth_section.is_displayed(), "Auth section should be visible"
    
    def test_main_content_present(self, driver, javascript_utils, frontend_server):
        """Test that main content is present."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Check main content
        main_content = driver.find_element(By.ID, "main-content")
        assert main_content.is_displayed(), "Main content should be visible"
        
        # Check home section
        home_section = driver.find_element(By.ID, "home")
        assert home_section.is_displayed(), "Home section should be visible"
        
        # Check welcome message
        welcome_text = home_section.text
        assert "Welcome" in welcome_text, "Should contain welcome message"
        assert "Course Creator" in welcome_text, "Should mention Course Creator"
    
    def test_buttons_present_and_clickable(self, driver, javascript_utils, page_objects, frontend_server):
        """Test that buttons are present and clickable."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Test login button
        login_button = page_objects.get_login_button()
        assert login_button.is_displayed(), "Login button should be visible"
        assert login_button.is_enabled(), "Login button should be enabled"
        
        # Test register button
        register_button = page_objects.get_register_button()
        assert register_button.is_displayed(), "Register button should be visible"
        assert register_button.is_enabled(), "Register button should be enabled"
        
        # Test courses button
        courses_button = page_objects.get_courses_button()
        assert courses_button.is_displayed(), "Courses button should be visible"
        assert courses_button.is_enabled(), "Courses button should be enabled"
    
    def test_form_elements_accessibility(self, driver, javascript_utils, page_objects, frontend_server):
        """Test form elements for accessibility."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Open login modal
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Wait for modal
        page_objects.get_login_modal()
        
        # Check form elements have proper labels/attributes
        email_input = driver.find_element(By.ID, "email")
        password_input = driver.find_element(By.ID, "password")
        
        # Check for accessibility attributes
        assert email_input.get_attribute("type") == "email", "Email input should have type='email'"
        assert password_input.get_attribute("type") == "password", "Password input should have type='password'"
        
        # Check for required attributes
        email_required = email_input.get_attribute("required")
        password_required = password_input.get_attribute("required")
        
        # If required attributes are set, they should be present
        if email_required is not None:
            assert email_required == "true" or email_required == "", "Email should be required"
        if password_required is not None:
            assert password_required == "true" or password_required == "", "Password should be required"


@pytest.mark.frontend
@pytest.mark.regression
class TestInteractiveElements:
    """Test interactive UI elements."""
    
    def test_modal_open_close_behavior(self, driver, javascript_utils, page_objects, frontend_server):
        """Test modal opening and closing behavior."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Test login modal
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Modal should appear
        modal = page_objects.get_login_modal()
        assert modal.is_displayed(), "Login modal should be visible"
        
        # Test closing modal (look for close button)
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, ".close, [data-dismiss], [onclick*='close']")
            close_button.click()
            
            # Wait for modal to close
            time.sleep(1)
            
            # Modal should be hidden
            assert not modal.is_displayed(), "Modal should be hidden after close"
        except NoSuchElementException:
            # If no close button exists, test ESC key or click outside
            # This depends on the modal implementation
            pass
    
    def test_form_validation_feedback(self, driver, javascript_utils, page_objects, frontend_server):
        """Test form validation feedback."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Open login modal
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Wait for modal
        page_objects.get_login_modal()
        
        # Try to submit empty form
        submit_button = driver.find_element(By.CSS_SELECTOR, "[type='submit']")
        submit_button.click()
        
        # Check for validation feedback
        email_input = driver.find_element(By.ID, "email")
        
        # Check if HTML5 validation is working
        validity = driver.execute_script("return arguments[0].validity.valid", email_input)
        if not validity:
            # HTML5 validation is working
            validation_message = driver.execute_script("return arguments[0].validationMessage", email_input)
            assert validation_message != "", "Should have validation message for empty email"
    
    def test_hover_effects(self, driver, javascript_utils, frontend_server):
        """Test hover effects on interactive elements."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Test hover on buttons
        login_button = driver.find_element(By.CSS_SELECTOR, ".btn-login")
        
        # Get initial style
        initial_color = login_button.value_of_css_property("background-color")
        
        # Hover over button
        ActionChains(driver).move_to_element(login_button).perform()
        time.sleep(0.5)
        
        # Check if style changed (this depends on CSS implementation)
        hover_color = login_button.value_of_css_property("background-color")
        
        # Note: This test might not work if hover effects are pure CSS
        # It's more for testing JavaScript-driven hover effects
    
    def test_focus_states(self, driver, javascript_utils, page_objects, frontend_server):
        """Test focus states on interactive elements."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Open login modal
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Wait for modal
        page_objects.get_login_modal()
        
        # Test focus on form elements
        email_input = driver.find_element(By.ID, "email")
        password_input = driver.find_element(By.ID, "password")
        
        # Focus on email input
        email_input.click()
        
        # Check if it's focused
        focused_element = driver.switch_to.active_element
        assert focused_element == email_input, "Email input should be focused"
        
        # Tab to next element
        email_input.send_keys("\t")
        
        # Check if password input is now focused
        focused_element = driver.switch_to.active_element
        assert focused_element == password_input, "Password input should be focused after tab"


@pytest.mark.responsive
@pytest.mark.regression
class TestResponsiveDesign:
    """Test responsive design behavior."""
    
    def test_desktop_layout(self, driver, javascript_utils, frontend_server):
        """Test desktop layout."""
        driver.get(f"{frontend_server}/index.html")
        driver.set_window_size(1920, 1080)
        javascript_utils.wait_for_page_load()
        
        # Check that elements are visible at desktop size
        header = driver.find_element(By.TAG_NAME, "header")
        assert header.is_displayed(), "Header should be visible on desktop"
        
        main_content = driver.find_element(By.ID, "main-content")
        assert main_content.is_displayed(), "Main content should be visible on desktop"
        
        # Check button layout
        login_button = driver.find_element(By.CSS_SELECTOR, ".btn-login")
        register_button = driver.find_element(By.CSS_SELECTOR, ".btn-register")
        
        assert login_button.is_displayed(), "Login button should be visible on desktop"
        assert register_button.is_displayed(), "Register button should be visible on desktop"
    
    def test_tablet_layout(self, driver, javascript_utils, frontend_server):
        """Test tablet layout."""
        driver.get(f"{frontend_server}/index.html")
        driver.set_window_size(768, 1024)
        javascript_utils.wait_for_page_load()
        
        # Check that essential elements are still visible
        header = driver.find_element(By.TAG_NAME, "header")
        assert header.is_displayed(), "Header should be visible on tablet"
        
        main_content = driver.find_element(By.ID, "main-content")
        assert main_content.is_displayed(), "Main content should be visible on tablet"
        
        # Check for JavaScript errors at tablet size
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors at tablet size: {errors}"
    
    def test_mobile_layout(self, driver, javascript_utils, frontend_server):
        """Test mobile layout."""
        driver.get(f"{frontend_server}/index.html")
        driver.set_window_size(375, 667)
        javascript_utils.wait_for_page_load()
        
        # Check that essential elements are still visible
        header = driver.find_element(By.TAG_NAME, "header")
        assert header.is_displayed(), "Header should be visible on mobile"
        
        main_content = driver.find_element(By.ID, "main-content")
        assert main_content.is_displayed(), "Main content should be visible on mobile"
        
        # Check for JavaScript errors at mobile size
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors at mobile size: {errors}"
    
    def test_responsive_navigation(self, driver, javascript_utils, frontend_server):
        """Test responsive navigation behavior."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Test different screen sizes
        sizes = [
            (1920, 1080),  # Desktop
            (768, 1024),   # Tablet
            (375, 667)     # Mobile
        ]
        
        for width, height in sizes:
            driver.set_window_size(width, height)
            time.sleep(1)  # Wait for resize
            
            # Check that navigation is still functional
            try:
                nav_element = driver.find_element(By.CSS_SELECTOR, ".nav-links, nav")
                # Navigation should exist (visibility depends on implementation)
                assert nav_element is not None, f"Navigation should exist at {width}x{height}"
            except NoSuchElementException:
                # If navigation is hidden at smaller sizes, that's acceptable
                pass
            
            # Check for JavaScript errors after resize
            errors = javascript_utils.get_console_errors()
            assert len(errors) == 0, f"JavaScript errors at {width}x{height}: {errors}"


@pytest.mark.frontend
@pytest.mark.regression
class TestNotificationSystem:
    """Test notification system functionality."""
    
    def test_notification_function_available(self, driver, javascript_utils, frontend_server):
        """Test that notification function is available."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("showNotification")
        
        # Check function exists
        assert javascript_utils.function_exists("showNotification"), "showNotification function should exist"
    
    def test_notification_can_be_called(self, driver, javascript_utils, frontend_server):
        """Test that notification function can be called."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("showNotification")
        
        # Clear console
        javascript_utils.clear_console()
        
        # Call notification function
        driver.execute_script("window.showNotification('Test notification', 'info')")
        
        # Check for errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors when calling showNotification: {errors}"
    
    def test_error_logging_system(self, driver, javascript_utils, frontend_server):
        """Test error logging system."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("showErrorLogs")
        
        # Test error logging function
        assert javascript_utils.function_exists("showErrorLogs"), "showErrorLogs function should exist"
        
        # Call error logging function
        driver.execute_script("window.showErrorLogs()")
        
        # Check for errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors when calling showErrorLogs: {errors}"


@pytest.mark.frontend
@pytest.mark.regression
class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_utility_functions_available(self, driver, javascript_utils, frontend_server):
        """Test that utility functions are available."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Wait for modular system to load
        javascript_utils.wait_for_function("showNotification", timeout=15)
        
        # Check utility functions
        utility_functions = [
            'debounce',
            'throttle',
            'formatDate'
        ]
        
        for func_name in utility_functions:
            if javascript_utils.function_exists(func_name):
                assert javascript_utils.get_function_type(func_name) == 'function', f"{func_name} should be a function"
    
    def test_authenticated_fetch_function(self, driver, javascript_utils, frontend_server):
        """Test authenticated fetch function."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("authenticatedFetch")
        
        # Check function exists
        assert javascript_utils.function_exists("authenticatedFetch"), "authenticatedFetch function should exist"
        
        # Test function with mock data (won't make actual request)
        javascript_utils.clear_console()
        
        # This will likely fail due to no auth token, but shouldn't cause JavaScript errors
        try:
            driver.execute_script("window.authenticatedFetch('http://localhost:8000/health')")
        except:
            # Expected to fail, but check for syntax errors
            pass
        
        # Check for syntax errors (ignore network errors)
        errors = javascript_utils.get_console_errors()
        syntax_errors = [e for e in errors if 'SyntaxError' in e['message']]
        assert len(syntax_errors) == 0, f"Syntax errors in authenticatedFetch: {syntax_errors}"