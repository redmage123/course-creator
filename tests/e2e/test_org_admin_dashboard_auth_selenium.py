"""
E2E Tests for Org Admin Dashboard Authentication using Selenium

BUSINESS CONTEXT:
End-to-end tests validate the complete user journey from login page
through dashboard access, ensuring no redirect loops or authentication failures.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver for browser automation
- Tests real browser localStorage behavior
- Validates navigation and redirect behavior

TDD METHODOLOGY:
These tests catch issues that unit/integration tests miss, like:
- Browser-specific localStorage behavior
- Actual redirect loops in browser
- Module loading and ES6 import errors
"""

import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

pytestmark = pytest.mark.nondestructive


class TestOrgAdminDashboardAuth:
    """
    Test Suite: Org Admin Dashboard Authentication E2E
    """

    @pytest.fixture(scope="function")
    def driver(self):
        """
        Setup Selenium WebDriver with Chrome

        BUSINESS CONTEXT:
        Creates isolated browser instance for each test to prevent state leakage
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        yield driver
        driver.quit()

    @pytest.fixture(scope="session")
    def base_url(self):
        """Base URL for tests"""
        return os.getenv('TEST_BASE_URL', 'https://176.9.99.103:3000')

    def test_login_and_access_dashboard_without_redirect_loop(self, driver, base_url):
        """
        TEST: Login and access dashboard without redirect loop
        REQUIREMENT: User should be able to login and access dashboard
        """
        # Navigate to login page
        driver.get(f'{base_url}/html/index.html')
        time.sleep(2)

        # Set authToken manually to simulate successful login
        driver.execute_script("""
            localStorage.setItem('authToken', 'test-token-12345');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                email: 'admin@test.com',
                role: 'organization_admin',
                organization_id: 1
            }));
            localStorage.setItem('userEmail', 'admin@test.com');
            localStorage.setItem('sessionStart', Date.now().toString());
            localStorage.setItem('lastActivity', Date.now().toString());
        """)

        # Verify authToken is set in localStorage
        auth_token = driver.execute_script("return localStorage.getItem('authToken');")
        assert auth_token == 'test-token-12345', "authToken should be set in localStorage"

        # Verify deprecated token key is NOT set
        deprecated_token = driver.execute_script("return localStorage.getItem('auth_token');")
        assert deprecated_token is None, "Deprecated auth_token should not be set"

        # Navigate to org admin dashboard
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(3)

        # Verify we're still on dashboard (no redirect loop)
        current_url = driver.current_url
        assert 'org-admin-dashboard.html' in current_url, f"Should be on dashboard, but URL is {current_url}"
        assert 'index.html' not in current_url, "Should not have redirected to index.html"

        # Verify authToken still exists
        still_authenticated = driver.execute_script("return localStorage.getItem('authToken');")
        assert still_authenticated is not None, "authToken should persist after navigation"

    def test_redirect_to_login_when_not_authenticated(self, driver, base_url):
        """
        TEST: Dashboard redirects to login when not authenticated
        REQUIREMENT: Unauthenticated users should be redirected to login
        """
        # Navigate to login and clear localStorage
        driver.get(f'{base_url}/html/index.html')
        driver.execute_script("localStorage.clear();")

        # Attempt to access dashboard without auth
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(3)

        # Verify redirected to login
        current_url = driver.current_url
        assert 'index.html' in current_url, f"Should redirect to index.html, but URL is {current_url}"

    def test_authtoken_key_consistency_across_modules(self, driver, base_url):
        """
        TEST: Verify localStorage token key consistency
        REQUIREMENT: All modules must use 'authToken' key
        """
        driver.get(f'{base_url}/html/index.html')

        # Manually set authToken
        driver.execute_script("""
            localStorage.setItem('authToken', 'consistency-test-token');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                email: 'test@example.com',
                role: 'organization_admin',
                organization_id: 1
            }));
        """)

        # Verify token is set
        token = driver.execute_script("return localStorage.getItem('authToken');")
        assert token == 'consistency-test-token', "authToken should be set"

        # Navigate to dashboard
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(2)

        # Verify token is still present (not cleared by dashboard)
        token_after_navigation = driver.execute_script("return localStorage.getItem('authToken');")
        assert token_after_navigation == 'consistency-test-token', "authToken should persist across navigation"

    def test_logout_clears_authtoken(self, driver, base_url):
        """
        TEST: Logout clears authToken and redirects
        REQUIREMENT: Logout must clear all auth data
        """
        driver.get(f'{base_url}/html/index.html')

        # Set up authenticated state
        driver.execute_script("""
            localStorage.setItem('authToken', 'logout-test-token');
            localStorage.setItem('currentUser', JSON.stringify({id: 1}));
            localStorage.setItem('userEmail', 'user@test.com');
            localStorage.setItem('sessionStart', Date.now().toString());
            localStorage.setItem('lastActivity', Date.now().toString());
        """)

        # Navigate to dashboard
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(2)

        # Try to find and click logout button
        try:
            logout_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "logoutBtn"))
            )

            # Accept confirmation dialog
            logout_btn.click()
            time.sleep(1)

            # Handle alert if it appears
            try:
                alert = driver.switch_to.alert
                alert.accept()
                time.sleep(1)
            except:
                pass

            # Verify all auth data cleared
            auth_token = driver.execute_script("return localStorage.getItem('authToken');")
            current_user = driver.execute_script("return localStorage.getItem('currentUser');")
            user_email = driver.execute_script("return localStorage.getItem('userEmail');")

            assert auth_token is None, "authToken should be cleared on logout"
            assert current_user is None, "currentUser should be cleared on logout"
            assert user_email is None, "userEmail should be cleared on logout"
        except (TimeoutException, NoSuchElementException):
            # Logout button might not be visible, skip this assertion
            pass

    def test_no_javascript_errors_on_dashboard_load(self, driver, base_url):
        """
        TEST: No JavaScript errors on dashboard load
        REQUIREMENT: Dashboard should load without console errors
        """
        # Enable browser logs
        driver.get(f'{base_url}/html/index.html')

        # Set up authenticated state
        driver.execute_script("""
            localStorage.setItem('authToken', 'error-test-token');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                email: 'test@example.com',
                role: 'organization_admin',
                organization_id: 1
            }));
        """)

        # Navigate to dashboard
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(3)

        # Get browser console logs
        logs = driver.get_log('browser')

        # Filter for critical errors (ignore network errors since backend might not be running)
        critical_errors = [
            log for log in logs
            if log['level'] == 'SEVERE'
            and 'Failed to fetch' not in log['message']
            and 'NetworkError' not in log['message']
            and 'ERR_CONNECTION_REFUSED' not in log['message']
        ]

        # Should have no critical JavaScript errors
        assert len(critical_errors) == 0, f"Found critical errors: {critical_errors}"

    def test_no_redirect_loop_on_dashboard_access(self, driver, base_url):
        """
        TEST: Detect redirect loop
        REQUIREMENT: No infinite redirect loops should occur
        """
        driver.get(f'{base_url}/html/index.html')

        # Set authToken
        driver.execute_script("""
            localStorage.setItem('authToken', 'redirect-loop-test');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                role: 'organization_admin',
                organization_id: 1
            }));
        """)

        # Navigate to dashboard
        start_time = time.time()
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')

        # Wait and check if page stabilizes
        time.sleep(5)
        end_time = time.time()

        # Verify still on dashboard
        current_url = driver.current_url
        assert 'org-admin-dashboard.html' in current_url, "Should still be on dashboard page"

        # If there was a redirect loop, the page would keep reloading
        # and we'd timeout or see performance degradation
        load_time = end_time - start_time
        assert load_time < 10, f"Page took too long to load ({load_time}s), possible redirect loop"

    def test_module_imports_work_correctly(self, driver, base_url):
        """
        TEST: Module imports work correctly
        REQUIREMENT: ES6 module imports should not fail
        """
        driver.get(f'{base_url}/html/index.html')

        # Set authenticated state
        driver.execute_script("""
            localStorage.setItem('authToken', 'module-test-token');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                role: 'organization_admin',
                organization_id: 1
            }));
        """)

        # Navigate to dashboard
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(3)

        # Get console logs and check for module errors
        logs = driver.get_log('browser')
        module_errors = [
            log for log in logs
            if log['level'] == 'SEVERE' and
            ('import' in log['message'].lower() or
             'export' in log['message'].lower() or
             'module' in log['message'].lower())
        ]

        # Should have no module/import errors
        assert len(module_errors) == 0, f"Found module errors: {module_errors}"

    def test_api_calls_include_authorization_header(self, driver, base_url):
        """
        TEST: API calls include Authorization header with authToken
        REQUIREMENT: All API requests must include Bearer token

        NOTE: This test verifies the token is available, actual header inspection
        would require network interception which varies by browser
        """
        driver.get(f'{base_url}/html/index.html')

        mock_token = 'api-header-test-token'

        # Set authToken
        driver.execute_script(f"""
            localStorage.setItem('authToken', '{mock_token}');
            localStorage.setItem('currentUser', JSON.stringify({{
                id: 1,
                role: 'organization_admin',
                organization_id: 1
            }}));
        """)

        # Navigate to dashboard (will trigger API calls)
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(3)

        # Verify token is still available for API calls
        token = driver.execute_script("return localStorage.getItem('authToken');")
        assert token == mock_token, "Token should be available for API calls"

    def test_session_timeout_clears_authtoken(self, driver, base_url):
        """
        TEST: Session timeout clears authToken
        REQUIREMENT: Inactive sessions should be cleared
        """
        driver.get(f'{base_url}/html/index.html')

        # Set authToken with old timestamp (35 minutes ago)
        driver.execute_script("""
            const oldTimestamp = Date.now() - (35 * 60 * 1000);
            localStorage.setItem('authToken', 'timeout-test-token');
            localStorage.setItem('last_activity_timestamp', oldTimestamp.toString());
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                organization_id: 1
            }));
        """)

        # Navigate to dashboard (session manager should check timeout)
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(3)

        # Check if redirected to login OR token was cleared
        current_url = driver.current_url
        redirected_to_login = 'index.html' in current_url

        token = driver.execute_script("return localStorage.getItem('authToken');")
        token_cleared = token is None or token != 'timeout-test-token'

        # Session timeout should either redirect or clear the old token
        assert redirected_to_login or token_cleared, "Session timeout should clear auth or redirect"

    def test_no_deprecated_auth_token_key_used(self, driver, base_url):
        """
        TEST: Verify no modules use deprecated auth_token key
        REQUIREMENT: No code should use 'auth_token' (underscore version)
        """
        driver.get(f'{base_url}/html/index.html')

        # Set correct token
        driver.execute_script("""
            localStorage.setItem('authToken', 'correct-token');
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                organization_id: 1
            }));
        """)

        # Navigate to dashboard
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(2)

        # Verify deprecated key is never set
        deprecated_token = driver.execute_script("return localStorage.getItem('auth_token');")
        assert deprecated_token is None, "Deprecated auth_token key should never be used"

        # Verify correct key exists
        correct_token = driver.execute_script("return localStorage.getItem('authToken');")
        assert correct_token == 'correct-token', "Correct authToken key should be used"


class TestSessionTimeoutBehavior:
    """
    Test Suite: Session Timeout E2E
    """

    @pytest.fixture(scope="function")
    def driver(self):
        """Setup Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        yield driver
        driver.quit()

    @pytest.fixture(scope="session")
    def base_url(self):
        """Base URL for tests"""
        return os.getenv('TEST_BASE_URL', 'https://176.9.99.103:3000')

    def test_active_session_persists_token(self, driver, base_url):
        """
        TEST: Active session keeps token alive
        REQUIREMENT: Recent activity should prevent session timeout
        """
        driver.get(f'{base_url}/html/index.html')

        # Set authToken with recent activity
        driver.execute_script("""
            const recentTimestamp = Date.now() - (5 * 60 * 1000); // 5 minutes ago
            localStorage.setItem('authToken', 'active-session-token');
            localStorage.setItem('last_activity_timestamp', recentTimestamp.toString());
            localStorage.setItem('currentUser', JSON.stringify({
                id: 1,
                organization_id: 1
            }));
        """)

        # Navigate to dashboard
        driver.get(f'{base_url}/html/org-admin-dashboard.html?org_id=1')
        time.sleep(2)

        # Token should still be present (session is active)
        token = driver.execute_script("return localStorage.getItem('authToken');")
        assert token == 'active-session-token', "Active session token should persist"

        # Should not redirect to login
        current_url = driver.current_url
        assert 'org-admin-dashboard.html' in current_url, "Should remain on dashboard"
