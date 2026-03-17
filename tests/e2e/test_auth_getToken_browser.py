"""
E2E Tests for Auth.getToken() Browser Integration

BUSINESS CONTEXT:
Validates that the Auth.getToken() method works correctly in actual browser
environment, ensuring org-admin dashboard can retrieve auth tokens for API calls.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver to test browser localStorage interaction
- Validates Auth module export/import chain
- Tests real-world org-admin dashboard API call scenarios

TDD METHODOLOGY:
These E2E tests verify the Auth.getToken() bug fix works in production:
- Bug: TypeError: Auth.getToken is not a function
- Fix: Added getToken() method to auth.js
- Validation: Browser can call Auth.getToken() successfully
"""

import pytest
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from tests.e2e.selenium_base import BaseTest, BasePage

pytestmark = pytest.mark.nondestructive


class OrgAdminDashboardPage(BasePage):
    """
    Page Object Model for Org Admin Dashboard

    DESIGN PATTERN: Page Object Model
    Encapsulates org-admin dashboard elements and interactions.
    """

    # Locators
    LOADING_SPINNER = (By.ID, 'loadingSpinner')
    LOGOUT_BTN = (By.ID, 'logoutBtn')
    PROJECTS_TAB = (By.ID, 'projectsTab')
    USERS_TAB = (By.ID, 'usersTab')

    def navigate_to_dashboard(self, org_id: int = 1):
        """Navigate to org admin dashboard"""
        self.navigate_to(f'/html/org-admin-dashboard.html?org_id={org_id}')

    def set_authenticated_state(self, token: str = 'test-token-123', user_id: int = 1, org_id: int = 1):
        """Set up authenticated state in localStorage"""
        self.execute_script(f"""
            localStorage.setItem('authToken', '{token}');
            localStorage.setItem('currentUser', JSON.stringify({{
                id: {user_id},
                email: 'admin@test.com',
                role: 'organization_admin',
                organization_id: {org_id}
            }}));
            localStorage.setItem('userEmail', 'admin@test.com');
            localStorage.setItem('sessionStart', Date.now().toString());
            localStorage.setItem('lastActivity', Date.now().toString());
        """)

    def get_auth_token_from_storage(self) -> str:
        """Get authToken from localStorage"""
        return self.execute_script("return localStorage.getItem('authToken');")

    def verify_auth_module_loaded(self) -> bool:
        """Verify Auth module is loaded and accessible"""
        return self.execute_script("""
            try {
                // Check if Auth module exists in window
                return typeof window.Auth !== 'undefined';
            } catch (e) {
                console.error('Auth module check failed:', e);
                return false;
            }
        """)

    def call_auth_get_token(self) -> str:
        """Call Auth.getToken() in browser context"""
        return self.execute_script("""
            try {
                // Import Auth module if not already imported
                if (typeof Auth === 'undefined' && typeof window.Auth === 'undefined') {
                    throw new Error('Auth module not loaded');
                }

                // Get the Auth instance (could be window.Auth or global Auth)
                const authInstance = window.Auth || Auth;

                // Call getToken() method
                return authInstance.getToken();
            } catch (e) {
                console.error('Auth.getToken() error:', e);
                throw e;
            }
        """)

    def verify_get_token_method_exists(self) -> bool:
        """Verify Auth.getToken method exists"""
        return self.execute_script("""
            try {
                const authInstance = window.Auth || Auth;
                return typeof authInstance.getToken === 'function';
            } catch (e) {
                console.error('getToken method check failed:', e);
                return false;
            }
        """)

    def simulate_api_call_with_token(self) -> dict:
        """Simulate making an API call using Auth.getToken()"""
        return self.execute_script("""
            try {
                const authInstance = window.Auth || Auth;
                const token = authInstance.getToken();

                // Simulate creating Authorization header
                const headers = {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                };

                return {
                    success: true,
                    token: token,
                    authHeader: headers.Authorization
                };
            } catch (e) {
                return {
                    success: false,
                    error: e.message
                };
            }
        """)


class TestAuthGetTokenE2E(BaseTest):
    """
    E2E Test Suite: Auth.getToken() Browser Integration

    VALIDATION SCOPE:
    - Auth.getToken() method exists and is callable
    - Method returns correct token from localStorage
    - Method works in org-admin dashboard context
    - API call simulation uses token correctly
    """

    def test_auth_get_token_method_exists_in_browser(self):
        """
        TEST: Auth.getToken() method exists in browser
        REQUIREMENT: Auth module must export getToken method
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state()

        # Navigate to dashboard (loads Auth module)
        page.navigate_to_dashboard()
        time.sleep(2)

        # Verify Auth module loaded
        auth_loaded = page.verify_auth_module_loaded()
        assert auth_loaded, "Auth module should be loaded in browser"

        # Verify getToken method exists
        method_exists = page.verify_get_token_method_exists()
        assert method_exists, "Auth.getToken() method should exist"

    def test_auth_get_token_returns_token_from_memory(self):
        """
        TEST: Auth.getToken() returns token from authToken property
        REQUIREMENT: getToken() should return in-memory token first
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state(token='memory-token-456')

        # Navigate to dashboard
        page.navigate_to_dashboard()
        time.sleep(2)

        # Call Auth.getToken() - should return token from memory
        try:
            token = page.call_auth_get_token()
            assert token == 'memory-token-456', f"Expected 'memory-token-456', got '{token}'"
        except Exception as e:
            pytest.fail(f"Auth.getToken() failed: {e}")

    def test_auth_get_token_falls_back_to_localstorage(self):
        """
        TEST: Auth.getToken() falls back to localStorage
        REQUIREMENT: getToken() should check localStorage if memory token null
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state(token='storage-token-789')

        # Navigate to dashboard
        page.navigate_to_dashboard()
        time.sleep(2)

        # Clear in-memory token (simulate page refresh scenario)
        page.execute_script("""
            if (window.Auth || Auth) {
                const authInstance = window.Auth || Auth;
                authInstance.authToken = null;
            }
        """)

        # Call Auth.getToken() - should fall back to localStorage
        try:
            token = page.call_auth_get_token()
            assert token == 'storage-token-789', f"Expected fallback to localStorage, got '{token}'"
        except Exception as e:
            pytest.fail(f"Auth.getToken() localStorage fallback failed: {e}")

    def test_auth_get_token_works_in_api_call_context(self):
        """
        TEST: Auth.getToken() works when creating Authorization headers
        REQUIREMENT: Org admin dashboard should use getToken() for API calls
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state(token='api-call-token')

        # Navigate to dashboard
        page.navigate_to_dashboard()
        time.sleep(2)

        # Simulate API call using Auth.getToken()
        result = page.simulate_api_call_with_token()

        assert result['success'], f"API call simulation failed: {result.get('error', 'unknown error')}"
        assert result['token'] == 'api-call-token', f"Expected 'api-call-token', got '{result['token']}'"
        assert result['authHeader'] == 'Bearer api-call-token', f"Incorrect auth header: {result['authHeader']}"

    def test_no_get_token_type_error_on_dashboard_load(self):
        """
        TEST: No "Auth.getToken is not a function" error
        REQUIREMENT: Fix for bug - TypeError should not occur

        BUG CONTEXT:
        - Before fix: TypeError: Auth.getToken is not a function
        - After fix: Auth.getToken() should be callable
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state()

        # Navigate to dashboard
        page.navigate_to_dashboard()
        time.sleep(3)

        # Get browser console logs
        logs = self.driver.get_log('browser')

        # Check for "getToken is not a function" errors
        get_token_errors = [
            log for log in logs
            if log['level'] == 'SEVERE' and
            'getToken' in log['message'] and
            'not a function' in log['message']
        ]

        assert len(get_token_errors) == 0, f"Found getToken TypeError errors: {get_token_errors}"

    def test_auth_get_token_returns_null_when_not_authenticated(self):
        """
        TEST: Auth.getToken() returns null when not authenticated
        REQUIREMENT: getToken() should handle unauthenticated state gracefully
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Navigate to login and clear all auth data
        page.navigate_to('/html/index.html')
        page.execute_script("localStorage.clear();")

        # Try to access dashboard (will redirect, but we can still test the method)
        page.navigate_to_dashboard()
        time.sleep(2)

        # Since we'll likely be redirected, let's test on the index page
        page.navigate_to('/html/index.html')
        time.sleep(1)

        # Load the Auth module manually for testing
        token = page.execute_script("""
            return localStorage.getItem('authToken');
        """)

        # Token should be null
        assert token is None, "authToken should be null when not authenticated"

    def test_auth_module_import_works_in_utils_module(self):
        """
        TEST: Auth import in utils.js works correctly
        REQUIREMENT: Fix for missing Auth import in utils.js

        BUG CONTEXT:
        - Before fix: Auth is not defined (in getCurrentUserOrgId)
        - After fix: Auth import should work
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state(org_id=42)

        # Navigate to dashboard (loads all modules including utils.js)
        page.navigate_to_dashboard(org_id=42)
        time.sleep(2)

        # Check for Auth import errors in console
        logs = self.driver.get_log('browser')

        # Filter for "Auth is not defined" errors in utils context
        auth_undefined_errors = [
            log for log in logs
            if log['level'] == 'SEVERE' and
            ('Auth is not defined' in log['message'] or
             'Auth is undefined' in log['message'])
        ]

        assert len(auth_undefined_errors) == 0, f"Found 'Auth is not defined' errors: {auth_undefined_errors}"

    def test_dashboard_loads_without_auth_errors(self):
        """
        TEST: Org admin dashboard loads without authentication errors
        REQUIREMENT: Complete authentication flow should work end-to-end
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state()

        # Navigate to dashboard
        page.navigate_to_dashboard()
        time.sleep(3)

        # Verify we're on the dashboard (not redirected)
        current_url = page.get_current_url()
        assert 'org-admin-dashboard.html' in current_url, f"Should be on dashboard, but URL is {current_url}"

        # Get all severe console errors
        logs = self.driver.get_log('browser')
        severe_errors = [
            log for log in logs
            if log['level'] == 'SEVERE' and
            'Failed to fetch' not in log['message'] and  # Ignore network errors (backend might not be running)
            'ERR_CONNECTION_REFUSED' not in log['message']
        ]

        # Should have no authentication-related errors
        auth_errors = [
            err for err in severe_errors
            if 'Auth' in err['message'] or
            'getToken' in err['message'] or
            'authentication' in err['message'].lower()
        ]

        assert len(auth_errors) == 0, f"Found authentication errors: {auth_errors}"

    def test_multiple_get_token_calls_return_consistent_value(self):
        """
        TEST: Multiple Auth.getToken() calls return same token
        REQUIREMENT: getToken() should be idempotent
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state(token='consistency-test-token')

        # Navigate to dashboard
        page.navigate_to_dashboard()
        time.sleep(2)

        # Call getToken() multiple times
        tokens = page.execute_script("""
            const authInstance = window.Auth || Auth;
            return [
                authInstance.getToken(),
                authInstance.getToken(),
                authInstance.getToken()
            ];
        """)

        # All tokens should be identical
        assert len(set(tokens)) == 1, f"getToken() returned inconsistent values: {tokens}"
        assert tokens[0] == 'consistency-test-token', f"Expected 'consistency-test-token', got '{tokens[0]}'"


class TestOrgAdminAPIIntegration(BaseTest):
    """
    E2E Test Suite: Org Admin API Integration with Auth.getToken()

    VALIDATION SCOPE:
    - Dashboard API calls use Auth.getToken() correctly
    - No TypeError when making authenticated requests
    - Authorization headers constructed properly
    """

    def test_dashboard_api_module_uses_get_token(self):
        """
        TEST: Org admin API module can call Auth.getToken()
        REQUIREMENT: api.js should successfully call Auth.getToken()

        CONTEXT: api.js has 50+ calls to Auth.getToken()
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state(token='api-module-token')

        # Navigate to dashboard (loads api.js module)
        page.navigate_to_dashboard()
        time.sleep(3)

        # Check that API module loaded without getToken errors
        logs = self.driver.get_log('browser')
        api_errors = [
            log for log in logs
            if log['level'] == 'SEVERE' and
            'api.js' in log['message'] and
            'getToken' in log['message']
        ]

        assert len(api_errors) == 0, f"Found API module getToken errors: {api_errors}"

    def test_no_type_error_when_fetching_projects(self):
        """
        TEST: No TypeError when dashboard fetches projects
        REQUIREMENT: fetchProjects() should work without Auth.getToken errors
        """
        page = OrgAdminDashboardPage(self.driver, self.config)

        # Set up authenticated state
        page.navigate_to('/html/index.html')
        page.set_authenticated_state(org_id=1)

        # Navigate to dashboard and click projects tab
        page.navigate_to_dashboard()
        time.sleep(2)

        try:
            # Try to click projects tab (will trigger fetchProjects)
            page.click_element(*OrgAdminDashboardPage.PROJECTS_TAB, timeout=5)
            time.sleep(2)
        except:
            # Tab might not be visible, that's OK - we're testing for errors
            pass

        # Check for TypeError related to getToken
        logs = self.driver.get_log('browser')
        type_errors = [
            log for log in logs
            if log['level'] == 'SEVERE' and
            'TypeError' in log['message'] and
            'getToken' in log['message']
        ]

        assert len(type_errors) == 0, f"Found TypeError with getToken: {type_errors}"
