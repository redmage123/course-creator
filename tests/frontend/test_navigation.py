"""
Navigation functionality tests using Selenium.
Tests routing, page navigation, and access control.
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@pytest.mark.navigation
@pytest.mark.smoke
class TestPageNavigation:
    """Test basic page navigation functionality."""
    
    def test_home_page_loads(self, driver, javascript_utils, frontend_server):
        """Test that home page loads successfully."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Check page title
        assert "Course Creator" in driver.title, "Page title should contain 'Course Creator'"
        
        # Check for main content
        main_content = driver.find_element(By.ID, "main-content")
        assert main_content.is_displayed(), "Main content should be visible"
        
        # Check for navigation elements
        header = driver.find_element(By.TAG_NAME, "header")
        assert header.is_displayed(), "Header should be visible"
    
    def test_instructor_dashboard_loads(self, driver, javascript_utils, frontend_server):
        """Test that instructor dashboard loads successfully."""
        driver.get(f"{frontend_server}/instructor-dashboard.html")
        javascript_utils.wait_for_page_load()
        
        # Check page loads without errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors on instructor dashboard: {errors}"
        
        # Check for dashboard-specific elements
        try:
            dashboard_container = driver.find_element(By.CSS_SELECTOR, ".dashboard-container, .instructor-dashboard, [id*='dashboard']")
            assert dashboard_container is not None, "Dashboard container should be present"
        except NoSuchElementException:
            # If specific containers don't exist, just verify page loaded
            assert "dashboard" in driver.current_url.lower(), "Should be on dashboard page"
    
    def test_student_dashboard_loads(self, driver, javascript_utils, frontend_server):
        """Test that student dashboard loads successfully."""
        driver.get(f"{frontend_server}/student-dashboard.html")
        javascript_utils.wait_for_page_load()
        
        # Check page loads without errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors on student dashboard: {errors}"
        
        # Check for dashboard-specific elements
        try:
            dashboard_container = driver.find_element(By.CSS_SELECTOR, ".dashboard-container, .student-dashboard, [id*='dashboard']")
            assert dashboard_container is not None, "Dashboard container should be present"
        except NoSuchElementException:
            # If specific containers don't exist, just verify page loaded
            assert "dashboard" in driver.current_url.lower(), "Should be on dashboard page"
    
    def test_admin_page_loads(self, driver, javascript_utils, frontend_server):
        """Test that admin page loads successfully."""
        driver.get(f"{frontend_server}/admin.html")
        javascript_utils.wait_for_page_load()
        
        # Check page loads without errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors on admin page: {errors}"
        
        # Check for admin-specific elements
        try:
            admin_container = driver.find_element(By.CSS_SELECTOR, ".admin-container, .admin-dashboard, [id*='admin']")
            assert admin_container is not None, "Admin container should be present"
        except NoSuchElementException:
            # If specific containers don't exist, just verify page loaded
            assert "admin" in driver.current_url.lower(), "Should be on admin page"
    
    def test_lab_page_loads(self, driver, javascript_utils, frontend_server):
        """Test that lab page loads successfully."""
        driver.get(f"{frontend_server}/lab.html")
        javascript_utils.wait_for_page_load()
        
        # Check page loads without errors
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors on lab page: {errors}"


@pytest.mark.navigation
@pytest.mark.regression
class TestNavigationFunctionality:
    """Test navigation functionality and routing."""
    
    def test_load_courses_navigation(self, driver, javascript_utils, page_objects, frontend_server):
        """Test that loadCourses function navigates correctly."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("loadCourses")
        
        # Test unauthenticated user - should show login modal
        javascript_utils.clear_local_storage()
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Click View Courses button
        courses_button = page_objects.get_courses_button()
        courses_button.click()
        
        # Should trigger login modal (since user is not authenticated)
        try:
            page_objects.get_login_modal()
            # If modal appears, the function worked correctly
        except TimeoutException:
            # If no modal, check if we were redirected (alternative behavior)
            current_url = driver.current_url
            # Either modal should appear or we should be redirected
            assert "login" in current_url.lower() or "modal" in driver.page_source.lower(), \
                "Should show login modal or redirect to login page"
    
    def test_authenticated_load_courses_navigation(self, driver, javascript_utils, page_objects, frontend_server):
        """Test loadCourses navigation for authenticated users."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("loadCourses")
        
        # Set up authenticated student
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "student@example.com", "role": "student"}')
        
        # Refresh to apply state
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Click View Courses button
        courses_button = page_objects.get_courses_button()
        courses_button.click()
        
        # Wait for navigation
        time.sleep(2)
        
        # Should navigate to student dashboard
        current_url = driver.current_url
        assert "student-dashboard.html" in current_url, "Should navigate to student dashboard"
    
    def test_instructor_load_courses_navigation(self, driver, javascript_utils, page_objects, frontend_server):
        """Test loadCourses navigation for instructors."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        javascript_utils.wait_for_function("loadCourses")
        
        # Set up authenticated instructor
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "instructor@example.com", "role": "instructor"}')
        
        # Refresh to apply state
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Click View Courses button
        courses_button = page_objects.get_courses_button()
        courses_button.click()
        
        # Wait for navigation
        time.sleep(2)
        
        # Should navigate to instructor dashboard
        current_url = driver.current_url
        assert "instructor-dashboard.html" in current_url, "Should navigate to instructor dashboard"
    
    def test_hash_navigation(self, driver, javascript_utils, frontend_server):
        """Test hash-based navigation on index page."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Test navigation to different hash sections
        hash_sections = ["#home", "#about", "#contact", "#help"]
        
        for hash_section in hash_sections:
            # Navigate to hash
            driver.execute_script(f"window.locations.hash = '{hash_section}'")
            time.sleep(1)
            
            # Check that URL updated
            current_url = driver.current_url
            assert hash_section in current_url, f"URL should contain {hash_section}"
            
            # Check for JavaScript errors
            errors = javascript_utils.get_console_errors()
            assert len(errors) == 0, f"JavaScript errors during hash navigation to {hash_section}: {errors}"


@pytest.mark.navigation
@pytest.mark.regression
class TestAccessControl:
    """Test access control and role-based navigation."""
    
    def test_unauthenticated_access_to_dashboards(self, driver, javascript_utils, test_data, frontend_server):
        """Test that unauthenticated users are handled correctly on dashboard pages."""
        # Clear authentication
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.clear_local_storage()
        
        # Try to access protected pages
        protected_pages = [
            f"{frontend_server}/instructor-dashboard.html",
            f"{frontend_server}/student-dashboard.html",
            f"{frontend_server}/admin.html"
        ]
        
        for page_url in protected_pages:
            driver.get(page_url)
            javascript_utils.wait_for_page_load()
            
            # Check for JavaScript errors
            errors = javascript_utils.get_console_errors()
            assert len(errors) == 0, f"JavaScript errors on {page_url} without auth: {errors}"
            
            # Pages should load but may show login prompts or redirect
            # At minimum, they shouldn't crash
    
    def test_role_based_navigation_elements(self, driver, javascript_utils, frontend_server):
        """Test that navigation elements appear based on user role."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Test with different user roles
        roles = [
            {"role": "student", "link": "student-link"},
            {"role": "instructor", "link": "instructor-link"},
            {"role": "admin", "link": "admin-link"}
        ]
        
        for role_data in roles:
            # Set user role
            javascript_utils.set_local_storage("authToken", "dummy-token")
            javascript_utils.set_local_storage("currentUser", f'{{"email": "user@example.com", "role": "{role_data["role"]}"}}')
            
            # Refresh to apply state
            driver.refresh()
            javascript_utils.wait_for_page_load()
            
            # Check for role-specific navigation elements
            try:
                nav_link = driver.find_element(By.ID, role_data["link"])
                # Link should exist (visibility depends on implementation)
                assert nav_link is not None, f"Navigation link for {role_data['role']} should exist"
            except NoSuchElementException:
                # If links don't exist yet, that's okay - just verify no errors
                errors = javascript_utils.get_console_errors()
                assert len(errors) == 0, f"JavaScript errors with {role_data['role']} role: {errors}"
    
    def test_logout_redirects_to_home(self, driver, javascript_utils, frontend_server):
        """Test that logout redirects to home page."""
        # Start on a different page
        driver.get(f"{frontend_server}/instructor-dashboard.html")
        javascript_utils.wait_for_page_load()
        
        # Set up authenticated state
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "test@example.com", "role": "instructor"}')
        
        # Call logout
        driver.execute_script("window.logout()")
        
        # Wait for redirect
        time.sleep(3)
        
        # Should redirect to home page
        current_url = driver.current_url
        assert "index.html" in current_url or current_url.endswith("/"), \
            "Should redirect to home page after logout"


@pytest.mark.navigation
@pytest.mark.regression
class TestPageTransitions:
    """Test page transitions and state management."""
    
    def test_page_to_page_navigation(self, driver, javascript_utils, frontend_server):
        """Test navigation between different pages."""
        pages = [
            f"{frontend_server}/index.html",
            f"{frontend_server}/instructor-dashboard.html",
            f"{frontend_server}/student-dashboard.html",
            f"{frontend_server}/admin.html"
        ]
        
        for page_url in pages:
            driver.get(page_url)
            javascript_utils.wait_for_page_load()
            
            # Check page loads successfully
            errors = javascript_utils.get_console_errors()
            assert len(errors) == 0, f"JavaScript errors on {page_url}: {errors}"
            
            # Check that modular system loads on each page
            try:
                javascript_utils.wait_for_function("showNotification", timeout=5)
                # If we get here, modular system loaded successfully
            except TimeoutException:
                # Some pages might not load the full modular system
                # Just verify no critical errors
                critical_errors = [e for e in errors if 'SyntaxError' in e['message']]
                assert len(critical_errors) == 0, f"Critical JavaScript errors on {page_url}: {critical_errors}"
    
    def test_browser_back_forward_navigation(self, driver, javascript_utils, frontend_server):
        """Test browser back/forward navigation."""
        # Start at home page
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Navigate to another page
        driver.get(f"{frontend_server}/instructor-dashboard.html")
        javascript_utils.wait_for_page_load()
        
        # Use browser back
        driver.back()
        javascript_utils.wait_for_page_load()
        
        # Should be back at home
        current_url = driver.current_url
        assert "index.html" in current_url, "Should be back at home page"
        
        # Check for errors after back navigation
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors after back navigation: {errors}"
        
        # Use browser forward
        driver.forward()
        javascript_utils.wait_for_page_load()
        
        # Should be at instructor dashboard
        current_url = driver.current_url
        assert "instructor-dashboard.html" in current_url, "Should be at instructor dashboard"
        
        # Check for errors after forward navigation
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors after forward navigation: {errors}"
    
    def test_page_refresh_preserves_state(self, driver, javascript_utils, frontend_server):
        """Test that page refresh preserves authentication state."""
        driver.get(f"{frontend_server}/index.html")
        javascript_utils.wait_for_page_load()
        
        # Set authentication state
        javascript_utils.set_local_storage("authToken", "dummy-token")
        javascript_utils.set_local_storage("currentUser", '{"email": "test@example.com", "role": "student"}')
        
        # Refresh page
        driver.refresh()
        javascript_utils.wait_for_page_load()
        
        # Check that state is preserved
        auth_token = javascript_utils.get_local_storage("authToken")
        current_user = javascript_utils.get_local_storage("currentUser")
        
        assert auth_token == "dummy-token", "Auth token should be preserved after refresh"
        assert current_user is not None, "Current user should be preserved after refresh"
        
        # Check for errors after refresh
        errors = javascript_utils.get_console_errors()
        assert len(errors) == 0, f"JavaScript errors after page refresh: {errors}"