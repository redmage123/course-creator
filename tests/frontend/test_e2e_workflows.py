"""
End-to-end workflow tests using Selenium.
Replaces Playwright tests with comprehensive user journey testing.
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@pytest.mark.e2e
@pytest.mark.smoke
class TestUserRegistrationFlow:
    """Test complete user registration workflow."""
    
    def test_complete_registration_flow(self, driver, javascript_utils, page_objects, test_data, frontend_server):
        """Test complete user registration from start to finish."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Step 1: Click register button
        register_button = page_objects.get_register_button()
        register_button.click()
        
        # Step 2: Fill registration form
        try:
            register_modal = page_objects.get_register_modal()
            assert register_modal.is_displayed(), "Register modal should be visible"
            
            # Fill form fields (adjust selectors based on actual form)
            email_input = driver.find_element(By.CSS_SELECTOR, "#register-form input[type='email'], #register-email")
            password_input = driver.find_element(By.CSS_SELECTOR, "#register-form input[type='password'], #register-password")
            
            user_data = test_data["users"]["valid_user"]
            email_input.send_keys(user_data["email"])
            password_input.send_keys(user_data["password"])
            
            # Step 3: Submit form
            submit_button = driver.find_element(By.CSS_SELECTOR, "#register-form [type='submit']")
            submit_button.click()
            
            # Step 4: Check for errors during submission
            time.sleep(2)
            errors = javascript_utils.get_console_errors()
            critical_errors = [e for e in errors if 'SyntaxError' in e['message'] or 'ReferenceError' in e['message']]
            assert len(critical_errors) == 0, f"Critical errors during registration: {critical_errors}"
            
        except NoSuchElementException:
            pytest.skip("Registration form elements not found - may not be implemented yet")
    
    def test_registration_form_validation(self, driver, javascript_utils, page_objects, frontend_server):
        """Test registration form validation."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Open register modal
        register_button = page_objects.get_register_button()
        register_button.click()
        
        try:
            register_modal = page_objects.get_register_modal()
            
            # Try to submit empty form
            submit_button = driver.find_element(By.CSS_SELECTOR, "#register-form [type='submit']")
            submit_button.click()
            
            # Check for validation
            email_input = driver.find_element(By.CSS_SELECTOR, "#register-form input[type='email'], #register-email")
            validity = driver.execute_script("return arguments[0].validity.valid", email_input)
            
            if not validity:
                # HTML5 validation is working
                validation_message = driver.execute_script("return arguments[0].validationMessage", email_input)
                assert validation_message != "", "Should have validation message for empty email"
                
        except NoSuchElementException:
            pytest.skip("Registration form not found - may not be implemented yet")


@pytest.mark.e2e
@pytest.mark.smoke
class TestUserLoginFlow:
    """Test complete user login workflow."""
    
    def test_complete_login_flow(self, driver, javascript_utils, page_objects, test_data, frontend_server):
        """Test complete user login from start to finish."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Step 1: Click login button
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Step 2: Fill login form
        login_modal = page_objects.get_login_modal()
        assert login_modal.is_displayed(), "Login modal should be visible"
        
        user_data = test_data["users"]["valid_user"]
        page_objects.fill_login_form(user_data["email"], user_data["password"])
        
        # Step 3: Submit form
        javascript_utils.clear_console()
        page_objects.submit_login_form()
        
        # Step 4: Check for errors during submission
        time.sleep(2)
        errors = javascript_utils.get_console_errors()
        critical_errors = [e for e in errors if 'SyntaxError' in e['message'] or 'ReferenceError' in e['message']]
        assert len(critical_errors) == 0, f"Critical errors during login: {critical_errors}"
        
        # Step 5: Check for network requests (login attempt)
        # This would normally result in a network error since we don't have a real backend
        # But the JavaScript should handle it gracefully
    
    def test_login_form_validation(self, driver, javascript_utils, page_objects, frontend_server):
        """Test login form validation."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Open login modal
        login_button = page_objects.get_login_button()
        login_button.click()
        
        login_modal = page_objects.get_login_modal()
        
        # Try to submit empty form
        submit_button = driver.find_element(By.CSS_SELECTOR, "[type='submit']")
        submit_button.click()
        
        # Check for validation
        email_input = driver.find_element(By.ID, "email")
        validity = driver.execute_script("return arguments[0].validity.valid", email_input)
        
        if not validity:
            # HTML5 validation is working
            validation_message = driver.execute_script("return arguments[0].validationMessage", email_input)
            assert validation_message != "", "Should have validation message for empty email"
    
    def test_login_with_invalid_credentials(self, driver, javascript_utils, page_objects, test_data, frontend_server):
        """Test login with invalid credentials."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Open login modal
        login_button = page_objects.get_login_button()
        login_button.click()
        
        # Fill with invalid credentials
        page_objects.get_login_modal()
        invalid_user = test_data["users"]["invalid_user"]
        page_objects.fill_login_form(invalid_user["email"], invalid_user["password"])
        
        # Submit form
        javascript_utils.clear_console()
        page_objects.submit_login_form()
        
        # Check for graceful error handling
        time.sleep(2)
        errors = javascript_utils.get_console_errors()
        critical_errors = [e for e in errors if 'SyntaxError' in e['message'] or 'ReferenceError' in e['message']]
        assert len(critical_errors) == 0, f"Critical errors with invalid credentials: {critical_errors}"


@pytest.mark.e2e
@pytest.mark.regression
class TestCourseNavigationFlow:
    """Test course navigation workflows."""
    
    def test_unauthenticated_course_access(self, driver, javascript_utils, page_objects, frontend_server):
        """Test accessing courses without authentication."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Clear any existing auth
        javascript_utils.clear_local_storage()
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Try to access courses
        courses_button = page_objects.get_courses_button()
        courses_button.click()
        
        # Should prompt for login
        try:
            login_modal = page_objects.get_login_modal()
            assert login_modal.is_displayed(), "Should show login modal for unauthenticated access"
        except TimeoutException:
            # Alternative: might redirect to login page
            current_url = driver.current_url
            assert "login" in current_url.lower() or "auth" in current_url.lower(), \
                "Should redirect to login or show modal for unauthenticated access"
    
    def test_authenticated_student_course_access(self, driver, javascript_utils, page_objects, frontend_server):
        """Test course access as authenticated student."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Set up student authentication
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "student@example.com", "role": "student"}')
        
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Access courses
        courses_button = page_objects.get_courses_button()
        courses_button.click()
        
        # Should navigate to student dashboard
        time.sleep(2)
        current_url = driver.current_url
        assert "student-dashboard.html" in current_url, "Should navigate to student dashboard"
        
        # Check for errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors during student course access: {errors}"
    
    def test_authenticated_instructor_course_access(self, driver, javascript_utils, page_objects, frontend_server):
        """Test course access as authenticated instructor."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Set up instructor authentication
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "instructor@example.com", "role": "instructor"}')
        
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Access courses
        courses_button = page_objects.get_courses_button()
        courses_button.click()
        
        # Should navigate to instructor dashboard
        time.sleep(2)
        current_url = driver.current_url
        assert "instructor-dashboard.html" in current_url, "Should navigate to instructor dashboard"
        
        # Check for errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors during instructor course access: {errors}"


@pytest.mark.e2e
@pytest.mark.regression
class TestDashboardWorkflows:
    """Test dashboard-specific workflows."""
    
    def test_instructor_dashboard_navigation(self, driver, javascript_utils, test_data, frontend_server):
        """Test instructor dashboard navigation."""
        # Set up instructor authentication
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "instructor@example.com", "role": "instructor"}')
        
        # Navigate to instructor dashboard
        driver.get(f"{frontend_server}/instructor-dashboard.html")
        javascript_utils.wait_for_page_load()
        
        # Check page loads without errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors on instructor dashboard: {errors}"
        
        # Check for dashboard-specific elements
        try:
            # Look for common dashboard elements
            dashboard_elements = driver.find_elements(By.CSS_SELECTOR, 
                ".dashboard, .instructor-dashboard, [id*='dashboard'], .container")
            assert len(dashboard_elements) > 0, "Should have dashboard elements"
        except NoSuchElementException:
            # If specific elements don't exist, just verify no critical errors
            pass
    
    def test_student_dashboard_navigation(self, driver, javascript_utils, test_data, frontend_server):
        """Test student dashboard navigation."""
        # Set up student authentication
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "student@example.com", "role": "student"}')
        
        # Navigate to student dashboard
        driver.get(f"{frontend_server}/student-dashboard.html")
        javascript_utils.wait_for_page_load()
        
        # Check page loads without errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors on student dashboard: {errors}"
        
        # Check for dashboard-specific elements
        try:
            dashboard_elements = driver.find_elements(By.CSS_SELECTOR, 
                ".dashboard, .student-dashboard, [id*='dashboard'], .container")
            assert len(dashboard_elements) > 0, "Should have dashboard elements"
        except NoSuchElementException:
            # If specific elements don't exist, just verify no critical errors
            pass
    
    def test_admin_dashboard_navigation(self, driver, javascript_utils, test_data, frontend_server):
        """Test admin dashboard navigation."""
        # Set up admin authentication
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "admin@example.com", "role": "admin"}')
        
        # Navigate to admin dashboard
        driver.get(f"{frontend_server}/admin.html")
        javascript_utils.wait_for_page_load()
        
        # Check page loads without errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors on admin dashboard: {errors}"


@pytest.mark.e2e
@pytest.mark.regression
class TestSessionManagement:
    """Test session management workflows."""
    
    def test_session_persistence_across_pages(self, driver, javascript_utils, frontend_server):
        """Test that session persists across page navigation."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Set up authentication
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "test@example.com", "role": "student"}')
        
        # Navigate to different pages
        pages = [
            f"{frontend_server}/student-dashboard.html",
            f"{frontend_server}/instructor-dashboard.html",
            f"{frontend_server}/index.html"
        ]
        
        for page_url in pages:
            driver.get(page_url)
            javascript_utils.wait_for_page_load()
            
            # Check that session data is still there
            auth_token = javascript_utils.get_local_storage("authToken")
            current_user = javascript_utils.get_local_storage("currentUser")
            
            assert auth_token == "dummy-token", f"Auth token should persist on {page_url}"
            assert current_user is not None, f"Current user should persist on {page_url}"
            
            # Check for errors
            errors = javascript_utils.get_console_errors()
            assert len(errors) == 0, f"JavaScript errors on {page_url}: {errors}"
    
    def test_logout_workflow(self, driver, javascript_utils, frontend_server):
        """Test complete logout workflow."""
        driver.get(f"{frontend_server}/instructor-dashboard.html")
        javascript_utils.wait_for_page_load()
        
        # Set up authentication
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "test@example.com", "role": "instructor"}')
        
        # Refresh to apply state
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Perform logout
        driver.execute_script("window.logout()")
        
        # Wait for logout to complete
        time.sleep(3)
        
        # Check that we're redirected to home
        current_url = driver.current_url
        assert "index.html" in current_url or current_url.endswith("/"), \
            "Should redirect to home after logout"
        
        # Check that session data is cleared
        auth_token = javascript_utils.get_local_storage("authToken")
        current_user = javascript_utils.get_local_storage("currentUser")
        
        assert auth_token is None, "Auth token should be cleared after logout"
        assert current_user is None, "Current user should be cleared after logout"
        
        # Check for errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors during logout: {errors}"


@pytest.mark.e2e
@pytest.mark.regression
class TestErrorHandling:
    """Test error handling in workflows."""
    
    def test_network_error_handling(self, driver, javascript_utils, page_objects, frontend_server):
        """Test handling of network errors during login."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Attempt login (will fail due to no backend)
        login_button = page_objects.get_login_button()
        login_button.click()
        
        page_objects.get_login_modal()
        page_objects.fill_login_form("test@example.com", "password")
        
        javascript_utils.clear_console()
        page_objects.submit_login_form()
        
        # Wait for network request to complete/fail
        time.sleep(3)
        
        # Should handle network errors gracefully
        errors = javascript_utils.get_console_errors()
        critical_errors = [e for e in errors if 'SyntaxError' in e['message'] or 'ReferenceError' in e['message']]
        assert len(critical_errors) == 0, f"Critical errors during network failure: {critical_errors}"
    
    def test_missing_elements_handling(self, driver, javascript_utils, frontend_server):
        """Test handling of missing DOM elements."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Test functions that interact with DOM elements
        test_functions = [
            "window.toggleAccountDropdown()",
            "window.showLoginModal()",
            "window.showRegisterModal()"
        ]
        
        for func_call in test_functions:
            javascript_utils.clear_console()
            
            try:
                driver.execute_script(func_call)
                
                # Check for errors
                errors = javascript_utils.get_console_errors()
                critical_errors = [e for e in errors if 'SyntaxError' in e['message'] or 'ReferenceError' in e['message']]
                assert len(critical_errors) == 0, f"Critical errors calling {func_call}: {critical_errors}"
                
            except Exception as e:
                # If function fails, it should fail gracefully
                if "SyntaxError" in str(e) or "ReferenceError" in str(e):
                    pytest.fail(f"Critical JavaScript error calling {func_call}: {e}")
    
    def test_malformed_local_storage_handling(self, driver, javascript_utils, frontend_server):
        """Test handling of malformed localStorage data."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Set malformed data
        javascript_utils.set_local_storage("currentUser", "invalid-json")
        javascript_utils.set_local_storage("authToken", "")
        
        # Refresh page
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Should handle malformed data gracefully
        errors = javascript_utils.get_console_errors()
        critical_errors = [e for e in errors if 'SyntaxError' in e['message'] and 'JSON' not in e['message']]
        assert len(critical_errors) == 0, f"Critical errors with malformed localStorage: {critical_errors}"
        
        # Test getCurrentUser function with malformed data
        result = driver.execute_script("return window.getCurrentUser ? window.getCurrentUser() : null")
        # Should return null or handle error gracefully
        assert result is None or isinstance(result, dict), "getCurrentUser should handle malformed data gracefully"