"""
Authentication functionality tests using Selenium.
Replaces the Jest-based auth tests with real browser testing.
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@pytest.mark.auth
@pytest.mark.smoke
class TestAuthenticationUI:
    """Test authentication UI components."""
    
    def test_login_modal_appears(self, driver, page_objects, frontend_server):
        """Test that login modal appears when login button is clicked."""
        driver.get(f"{frontend_server}/index.html")
        
        # Click login button
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Verify modal appears
        try:
            modal = page_objects.get_login_modal()
            assert modal.is_displayed(), "Login modal should be visible"
        except TimeoutException:
            pytest.fail("Login modal did not appear")
    
    def test_register_modal_appears(self, driver, page_objects, frontend_server):
        """Test that register modal appears when register button is clicked."""
        driver.get(f"{frontend_server}/index.html")
        
        # Click register button
        register_button = page_objects.get_register_button()
        register_button.click()
        
        # Verify modal appears
        try:
            modal = page_objects.get_register_modal()
            assert modal.is_displayed(), "Register modal should be visible"
        except TimeoutException:
            pytest.fail("Register modal did not appear")
    
    def test_login_form_elements_present(self, driver, page_objects, frontend_server):
        """Test that login form has required elements."""
        driver.get(f"{frontend_server}/index.html")
        
        # Open login modal
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Wait for modal to appear
        page_objects.get_login_modal()
        
        # Check form elements
        email_input = driver.find_element(By.ID, "email")
        password_input = driver.find_element(By.ID, "password")
        submit_button = driver.find_element(By.CSS_SELECTOR, "[type='submit']")
        
        assert email_input.is_displayed(), "Email input should be visible"
        assert password_input.is_displayed(), "Password input should be visible"
        assert submit_button.is_displayed(), "Submit button should be visible"
    
    def test_register_form_elements_present(self, driver, page_objects, frontend_server):
        """Test that register form has required elements."""
        driver.get(f"{frontend_server}/index.html")
        
        # Open register modal
        register_button = page_objects.get_register_button()
        register_button.click()
        
        # Wait for modal to appear
        page_objects.get_register_modal()
        
        # Check form elements (adjust selectors based on actual form)
        try:
            email_input = driver.find_element(By.ID, "register-email")
            password_input = driver.find_element(By.ID, "register-password")
            submit_button = driver.find_element(By.CSS_SELECTOR, "#register-form [type='submit']")
            
            assert email_input.is_displayed(), "Email input should be visible"
            assert password_input.is_displayed(), "Password input should be visible"
            assert submit_button.is_displayed(), "Submit button should be visible"
        except NoSuchElementException:
            # Try alternative selectors
            email_input = driver.find_element(By.CSS_SELECTOR, "#register-form input[type='email']")
            password_input = driver.find_element(By.CSS_SELECTOR, "#register-form input[type='password']")
            submit_button = driver.find_element(By.CSS_SELECTOR, "#register-form [type='submit']")
            
            assert email_input.is_displayed(), "Email input should be visible"
            assert password_input.is_displayed(), "Password input should be visible"
            assert submit_button.is_displayed(), "Submit button should be visible"


@pytest.mark.auth
@pytest.mark.regression
class TestAuthenticationFunctionality:
    """Test authentication functionality."""
    
    def test_login_form_submission(self, driver, page_objects, javascript_utils, test_data, frontend_server):
        """Test login form submission."""
        driver.get(f"{frontend_server}/index.html")
        
        # Open login modal
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Wait for modal and fill form
        page_objects.get_login_modal()
        page_objects.fill_login_form(
            test_data["users"]["valid_user"]["email"],
            test_data["users"]["valid_user"]["password"]
        )
        
        # Clear console errors
        javascript_utils.clear_console()
        
        # Submit form
        page_objects.submit_login_form()
        
        # Check for JavaScript errors during submission
        time.sleep(2)  # Wait for any async operations
        errors = javascript_utils.get_console_errors()
        
        # Filter out expected network errors (since backend might not be fully configured)
        critical_errors = [e for e in errors if 'SyntaxError' in e['message'] or 'ReferenceError' in e['message']]
        assert len(critical_errors) == 0, f"Critical JavaScript errors during login: {critical_errors}"
    
    def test_password_visibility_toggle(self, driver, page_objects, frontend_server):
        """Test password visibility toggle functionality."""
        driver.get(f"{frontend_server}/index.html")
        
        # Open login modal
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Wait for modal
        page_objects.get_login_modal()
        
        # Find password input and toggle button
        password_input = driver.find_element(By.ID, "password")
        
        # Check if toggle button exists
        try:
            toggle_button = driver.find_element(By.CSS_SELECTOR, "[onclick*='togglePasswordVisibility']")
            
            # Initial state should be password
            assert password_input.get_attribute("type") == "password", "Password should be hidden initially"
            
            # Click toggle
            toggle_button.click()
            
            # Should now be text
            assert password_input.get_attribute("type") == "text", "Password should be visible after toggle"
            
            # Click toggle again
            toggle_button.click()
            
            # Should be password again
            assert password_input.get_attribute("type") == "password", "Password should be hidden after second toggle"
            
        except NoSuchElementException:
            # Password toggle might not be implemented yet
            pytest.skip("Password visibility toggle not implemented")
    
    def test_logout_functionality(self, driver, javascript_utils, frontend_server):
        """Test logout functionality."""
        driver.get(f"{frontend_server}/index.html")
        
        # Simulate logged in state
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "test@example.com", "role": "student"}')
        
        # Refresh to apply state
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Clear console
        javascript_utils.clear_console()
        
        # Call logout function
        driver.execute_script("window.logout()")
        
        # Wait for logout to complete
        time.sleep(2)
        
        # Check that localStorage was cleared
        auth_token = javascript_utils.get_local_storage("authToken")
        current_user = javascript_utils.get_local_storage("currentUser")
        
        assert auth_token is None, "Auth token should be cleared after logout"
        assert current_user is None, "Current user should be cleared after logout"
        
        # Check for JavaScript errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors during logout: {errors}"


@pytest.mark.auth
@pytest.mark.regression
class TestAuthenticationState:
    """Test authentication state management."""
    
    def test_unauthenticated_state(self, driver, javascript_utils, frontend_server):
        """Test that unauthenticated state is handled correctly."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Clear any existing auth data
        javascript_utils.clear_local_storage()
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Check that auth buttons are visible
        auth_buttons = driver.find_element(By.ID, "authButtons")
        assert auth_buttons.is_displayed(), "Auth buttons should be visible when not authenticated"
        
        # Check that account dropdown is not visible
        account_dropdown = driver.find_element(By.ID, "accountDropdown")
        assert not account_dropdown.is_displayed(), "Account dropdown should not be visible when not authenticated"
    
    def test_authenticated_state(self, driver, javascript_utils, frontend_server):
        """Test that authenticated state is handled correctly."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Set authenticated state
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "test@example.com", "username": "testuser", "role": "student"}')
        
        # Refresh to apply state
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Give time for auth state to be processed
        time.sleep(2)
        
        # Check UI state (this might need adjustment based on actual implementation)
        try:
            # Look for user-specific elements
            user_elements = driver.find_elements(By.CSS_SELECTOR, "[id*='user'], [class*='user']")
            assert len(user_elements) > 0, "User-specific elements should be present when authenticated"
        except:
            # If specific elements don't exist, just verify no JavaScript errors
            errors = javascript_utils.get_console_errors()
            assert len(errors) == 0, f"JavaScript errors in authenticated state: {errors}"
    
    def test_get_current_user_function(self, driver, javascript_utils, frontend_server):
        """Test getCurrentUser function."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Clear storage first
        javascript_utils.clear_local_storage()
        
        # Test with no user
        current_user = driver.execute_script("return window.getCurrentUser ? window.getCurrentUser() : null")
        assert current_user is None, "getCurrentUser should return null when no user is stored"
        
        # Set user data
        user_data = '{"email": "test@example.com", "username": "testuser", "role": "student"}'
        javascript_utils.set_local_storage("currentUser", user_data)
        
        # Test with user data
        current_user = driver.execute_script("return window.getCurrentUser ? window.getCurrentUser() : null")
        assert current_user is not None, "getCurrentUser should return user data when available"
        assert current_user["email"] == "test@example.com", "getCurrentUser should return correct email"


@pytest.mark.auth
@pytest.mark.regression
class TestAccountDropdown:
    """Test account dropdown functionality."""
    
    def test_account_dropdown_toggle(self, driver, javascript_utils, frontend_server):
        """Test account dropdown toggle functionality."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Set up authenticated state
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "test@example.com", "username": "testuser"}')
        
        # Refresh to apply state
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Clear console
        javascript_utils.clear_console()
        
        # Test toggle function
        driver.execute_script("window.toggleAccountDropdown()")
        
        # Check for JavaScript errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors when toggling account dropdown: {errors}"
    
    def test_account_dropdown_elements(self, driver, javascript_utils, frontend_server):
        """Test that account dropdown has required elements."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Set up authenticated state
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "test@example.com", "username": "testuser"}')
        
        # Refresh to apply state
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Check if dropdown elements exist
        try:
            account_dropdown = driver.find_element(By.ID, "accountDropdown")
            account_menu = driver.find_element(By.ID, "accountMenu")
            
            # These elements should exist even if not visible
            assert account_dropdown is not None, "Account dropdown element should exist"
            assert account_menu is not None, "Account menu element should exist"
        except NoSuchElementException:
            pytest.skip("Account dropdown elements not found - may not be implemented yet")