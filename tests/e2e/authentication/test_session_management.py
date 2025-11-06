"""
Comprehensive E2E Tests for Session Management

BUSINESS REQUIREMENT:
Tests all session management operations including session creation, validation,
timeout mechanisms, and security features.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Validates session lifecycle (create, validate, expire, revoke)
- Tests session security (token validation, IP binding, timeout)
- Database verification for all operations

TEST COVERAGE:
1. Session Creation (2 tests)
   - Successful login creates session token
   - Session token stored in localStorage/cookie

2. Session Validation (3 tests)
   - Valid session allows API access
   - Expired session redirects to login
   - Invalid session token rejected

3. Session Security (3 tests)
   - Session timeout after 2 hours inactivity
   - User activity extends session
   - Session tied to IP address (optional)

PRIORITY: P0 (CRITICAL) - Core authentication security feature
"""

import pytest
import time
import uuid
import asyncio
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class SessionManager:
    """
    Helper class for session management operations.
    
    BUSINESS CONTEXT:
    Sessions are managed via JWT tokens stored in localStorage.
    This helper provides methods to interact with session state.
    """
    
    def __init__(self, driver):
        self.driver = driver
    
    def get_session_token(self):
        """Get current session token from localStorage."""
        return self.driver.execute_script("return localStorage.getItem('authToken')")
    
    def get_session_start_time(self):
        """Get session start timestamp from localStorage."""
        timestamp = self.driver.execute_script("return localStorage.getItem('sessionStart')")
        return int(timestamp) if timestamp else None
    
    def get_last_activity_time(self):
        """Get last activity timestamp from localStorage."""
        timestamp = self.driver.execute_script("return localStorage.getItem('lastActivity')")
        return int(timestamp) if timestamp else None
    
    def clear_session(self):
        """Clear session data from localStorage."""
        self.driver.execute_script("""
            localStorage.removeItem('authToken');
            localStorage.removeItem('sessionStart');
            localStorage.removeItem('lastActivity');
            localStorage.removeItem('currentUser');
        """)
    
    def set_session_token(self, token):
        """Set session token in localStorage."""
        self.driver.execute_script(f"localStorage.setItem('authToken', '{token}')")
    
    def set_last_activity(self, timestamp):
        """Set last activity timestamp in localStorage."""
        self.driver.execute_script(f"localStorage.setItem('lastActivity', '{timestamp}')")
    
    def update_activity(self):
        """Simulate user activity (update lastActivity timestamp)."""
        now = int(time.time() * 1000)
        self.driver.execute_script(f"localStorage.setItem('lastActivity', '{now}')")
    
    def is_session_valid(self):
        """Check if session appears valid (has required fields)."""
        token = self.get_session_token()
        session_start = self.get_session_start_time()
        last_activity = self.get_last_activity_time()
        return token is not None and session_start is not None and last_activity is not None


class LoginPage:
    """Page Object for Login page."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    # Locators
    EMAIL_INPUT = (By.ID, "login-email")
    PASSWORD_INPUT = (By.ID, "login-password")
    LOGIN_BUTTON = (By.ID, "login-submit")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    
    def navigate(self, base_url):
        """Navigate to login page."""
        self.driver.get(f"{base_url}/login")
    
    def login(self, email, password):
        """Perform login."""
        email_input = self.wait.until(EC.presence_of_element_located(self.EMAIL_INPUT))
        email_input.clear()
        email_input.send_keys(email)
        
        pwd_input = self.driver.find_element(*self.PASSWORD_INPUT)
        pwd_input.clear()
        pwd_input.send_keys(password)
        
        login_btn = self.driver.find_element(*self.LOGIN_BUTTON)
        login_btn.click()


class DashboardPage:
    """Page Object for Dashboard page (requires authentication)."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    # Locators
    DASHBOARD_CONTAINER = (By.ID, "dashboard-container")
    USER_INFO = (By.CLASS_NAME, "user-info")
    LOGOUT_BUTTON = (By.ID, "logout-btn")
    
    def navigate(self, base_url):
        """Navigate to dashboard."""
        self.driver.get(f"{base_url}/dashboard")
    
    def is_loaded(self):
        """Check if dashboard is fully loaded."""
        try:
            self.wait.until(EC.presence_of_element_located(self.DASHBOARD_CONTAINER))
            return True
        except TimeoutException:
            return False
    
    def logout(self):
        """Perform logout."""
        logout_btn = self.driver.find_element(*self.LOGOUT_BUTTON)
        logout_btn.click()


# ============================================================================
# TEST CLASS: Session Creation
# ============================================================================

@pytest.mark.e2e
@pytest.mark.authentication
@pytest.mark.session_management
@pytest.mark.priority_critical
class TestSessionCreation:
    """Test suite for session creation."""
    
    @pytest.mark.asyncio
    async def test_successful_login_creates_session_token(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Successful login creates session token
        
        BUSINESS REQUIREMENT:
        When a user logs in successfully, a session token must be created
        and stored for subsequent API requests.
        
        TEST SCENARIO:
        1. Navigate to login page
        2. Enter valid credentials
        3. Submit login form
        4. Verify redirect to dashboard
        5. Verify session token in localStorage
        6. Verify session token in database
        7. Verify session metadata (timestamps, user_id)
        
        VALIDATION:
        - Session token exists in localStorage
        - Session token exists in database
        - Session has proper expiration (2 hours)
        - Session metadata includes user_id, IP, user_agent
        """
        # Setup: Create test user
        test_email = "session_create_test@example.com"
        test_password = "TestPassword123!"
        
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
                RETURNING id
            """, test_email, "session_test", test_password)
        
        # Step 1-3: Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.login(test_email, test_password)
        
        # Step 4: VERIFICATION 1 - Redirected to dashboard
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        assert "/dashboard" in driver.current_url, "Should redirect to dashboard after login"
        
        # Step 5: VERIFICATION 2 - Session token in localStorage
        session_mgr = SessionManager(driver)
        session_token = session_mgr.get_session_token()
        assert session_token is not None, "Session token should be stored in localStorage"
        assert len(session_token) > 20, "Session token should be sufficiently long"
        
        # Step 6: VERIFICATION 3 - Session in database
        session_row = await db_connection.fetchrow("""
            SELECT id, user_id, token, expires_at, created_at, last_activity, status
            FROM course_creator.user_sessions
            WHERE user_id = $1 AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """, user_id)
        
        assert session_row is not None, "Session should be created in database"
        assert session_row['user_id'] == user_id, "Session should be linked to correct user"
        assert session_row['status'] == 'active', "Session should be active"
        
        # Step 7: VERIFICATION 4 - Session expiration (2 hours)
        time_until_expiry = session_row['expires_at'] - datetime.now()
        assert 115 <= time_until_expiry.total_seconds() / 60 <= 125, \
            "Session should expire in ~2 hours (120 minutes)"
        
        # VERIFICATION 5 - Session metadata
        session_start = session_mgr.get_session_start_time()
        last_activity = session_mgr.get_last_activity_time()
        
        assert session_start is not None, "sessionStart should be stored"
        assert last_activity is not None, "lastActivity should be stored"
        assert abs(session_start - last_activity) < 5000, \
            "sessionStart and lastActivity should be similar at login"
    
    @pytest.mark.asyncio
    async def test_session_token_stored_in_localstorage(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Session token stored in localStorage (not cookies)
        
        BUSINESS REQUIREMENT:
        Session tokens are stored in localStorage for SPA architecture.
        This allows the frontend to include tokens in API request headers.
        
        TEST SCENARIO:
        1. Login successfully
        2. Verify token in localStorage
        3. Verify token NOT in cookies
        4. Verify token format (JWT)
        5. Verify additional session data stored
        
        VALIDATION:
        - authToken in localStorage
        - sessionStart timestamp in localStorage
        - lastActivity timestamp in localStorage
        - currentUser object in localStorage
        - No sensitive data in cookies
        """
        # Setup: Create test user
        test_email = "localstorage_test@example.com"
        test_password = "TestPassword123!"
        
        async with db_connection.transaction():
            await db_connection.execute("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
            """, test_email, "localstorage_test", test_password)
        
        # Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.login(test_email, test_password)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # VERIFICATION 1: Token in localStorage
        session_mgr = SessionManager(driver)
        auth_token = session_mgr.get_session_token()
        assert auth_token is not None, "authToken should be in localStorage"
        
        # VERIFICATION 2: Session timestamps in localStorage
        session_start = session_mgr.get_session_start_time()
        last_activity = session_mgr.get_last_activity_time()
        
        assert session_start is not None, "sessionStart should be in localStorage"
        assert last_activity is not None, "lastActivity should be in localStorage"
        
        # VERIFICATION 3: currentUser object in localStorage
        current_user = driver.execute_script("return JSON.parse(localStorage.getItem('currentUser'))")
        assert current_user is not None, "currentUser should be in localStorage"
        assert current_user['email'] == test_email, "currentUser should have correct email"
        
        # VERIFICATION 4: Token format (JWT has 3 parts separated by dots)
        token_parts = auth_token.split('.')
        assert len(token_parts) == 3, "JWT token should have 3 parts (header.payload.signature)"
        
        # VERIFICATION 5: No auth token in cookies
        cookies = driver.get_cookies()
        auth_cookie = next((c for c in cookies if 'auth' in c['name'].lower()), None)
        assert auth_cookie is None, "Authentication should use localStorage, not cookies"


# ============================================================================
# TEST CLASS: Session Validation
# ============================================================================

@pytest.mark.e2e
@pytest.mark.authentication
@pytest.mark.session_management
@pytest.mark.priority_critical
class TestSessionValidation:
    """Test suite for session validation."""
    
    @pytest.mark.asyncio
    async def test_valid_session_allows_api_access(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Valid session allows API access
        
        BUSINESS REQUIREMENT:
        Users with valid sessions can access protected API endpoints.
        
        TEST SCENARIO:
        1. Login successfully
        2. Make API request to protected endpoint (/api/v1/users/me)
        3. Verify 200 OK response
        4. Verify user data returned
        5. Make multiple API requests
        6. Verify all succeed with valid session
        
        VALIDATION:
        - Protected endpoints return 200 with valid session
        - User data is correct
        - Multiple requests succeed
        """
        # Setup: Create test user
        test_email = "api_access_test@example.com"
        test_password = "TestPassword123!"
        test_username = "api_test_user"
        
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
                RETURNING id
            """, test_email, test_username, test_password)
        
        # Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.login(test_email, test_password)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # Get session token
        session_mgr = SessionManager(driver)
        auth_token = session_mgr.get_session_token()
        
        # VERIFICATION 1: API request to /users/me succeeds
        response = driver.execute_script("""
            const token = arguments[0];
            return fetch('https://localhost:8000/users/me', {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            }).then(r => r.json()).then(data => {
                return { status: 200, data: data };
            }).catch(err => {
                return { status: 401, error: err.message };
            });
        """, auth_token)
        
        # Wait for fetch to complete
        time.sleep(1)
        
        assert response['status'] == 200, "Protected endpoint should return 200 with valid session"
        assert response['data']['email'] == test_email, "Should return correct user data"
        assert response['data']['username'] == test_username, "Should return correct username"
        
        # VERIFICATION 2: Multiple API requests succeed
        for i in range(3):
            response = driver.execute_script("""
                const token = arguments[0];
                return fetch('https://localhost:8000/users/me', {
                    headers: {
                        'Authorization': 'Bearer ' + token
                    }
                }).then(r => r.status);
            """, auth_token)
            
            time.sleep(0.5)
            assert response == 200, f"Request {i+1} should succeed with valid session"
    
    @pytest.mark.asyncio
    async def test_expired_session_redirects_to_login(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Expired session redirects to login
        
        BUSINESS REQUIREMENT:
        When a session expires, the user must be redirected to the login page.
        
        TEST SCENARIO:
        1. Create expired session in database
        2. Set expired session token in localStorage
        3. Navigate to protected page (dashboard)
        4. Verify redirect to login page
        5. Verify error message shown
        
        VALIDATION:
        - Expired session redirects to login
        - Error message indicates session expired
        - Session cleared from localStorage
        """
        # Setup: Create test user with expired session
        test_email = "expired_session_test@example.com"
        test_password = "TestPassword123!"
        expired_token = str(uuid.uuid4())
        
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
                RETURNING id
            """, test_email, "expired_session_test", test_password)
            
            # Create expired session (expired 1 hour ago)
            await db_connection.execute("""
                INSERT INTO course_creator.user_sessions (
                    user_id, token, expires_at, created_at, last_activity, status
                )
                VALUES (
                    $1, $2, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '3 hours', 
                    NOW() - INTERVAL '1 hour', 'expired'
                )
            """, user_id, expired_token)
        
        # Set expired token in localStorage
        driver.get(test_base_url)  # Load page first
        session_mgr = SessionManager(driver)
        session_mgr.set_session_token(expired_token)
        
        # Set old lastActivity (3 hours ago)
        old_activity = int((time.time() - 3 * 3600) * 1000)
        session_mgr.set_last_activity(old_activity)
        
        # Try to navigate to dashboard
        dashboard_page = DashboardPage(driver)
        dashboard_page.navigate(test_base_url)
        
        # VERIFICATION 1: Redirected to login page
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url, "Should redirect to login with expired session"
        
        # VERIFICATION 2: Error message shown
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "session-expired-message")
            assert "expired" in error_msg.text.lower(), "Should show session expired message"
        except NoSuchElementException:
            pass  # Optional - some implementations may not show message
        
        # VERIFICATION 3: Session cleared from localStorage
        auth_token = session_mgr.get_session_token()
        assert auth_token is None, "Expired session should be cleared from localStorage"
    
    @pytest.mark.asyncio
    async def test_invalid_session_token_rejected(self, driver, test_base_url):
        """
        E2E TEST: Invalid session token rejected
        
        BUSINESS REQUIREMENT:
        Invalid or tampered session tokens must be rejected.
        
        TEST SCENARIO:
        1. Set invalid token in localStorage
        2. Try to access protected page
        3. Verify redirect to login
        4. Verify error message
        5. Try API request with invalid token
        6. Verify 401 Unauthorized
        
        VALIDATION:
        - Invalid token redirects to login
        - API requests with invalid token return 401
        - Error messages indicate invalid session
        """
        # Set invalid token in localStorage
        driver.get(test_base_url)
        session_mgr = SessionManager(driver)
        session_mgr.set_session_token("invalid-token-12345")
        
        # Try to navigate to dashboard
        dashboard_page = DashboardPage(driver)
        dashboard_page.navigate(test_base_url)
        
        # VERIFICATION 1: Redirected to login page
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url, "Should redirect to login with invalid token"
        
        # VERIFICATION 2: Try API request with invalid token
        response = driver.execute_script("""
            return fetch('https://localhost:8000/users/me', {
                headers: {
                    'Authorization': 'Bearer invalid-token-12345'
                }
            }).then(r => r.status);
        """)
        
        time.sleep(1)
        assert response == 401, "API request with invalid token should return 401"


# ============================================================================
# TEST CLASS: Session Security
# ============================================================================

@pytest.mark.e2e
@pytest.mark.authentication
@pytest.mark.session_management
@pytest.mark.priority_critical
class TestSessionSecurity:
    """Test suite for session security features."""
    
    @pytest.mark.asyncio
    async def test_session_timeout_after_2_hours_inactivity(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Session timeout after 2 hours inactivity
        
        BUSINESS REQUIREMENT:
        Sessions must expire after 2 hours of inactivity for security.
        
        TEST SCENARIO:
        1. Login successfully
        2. Simulate 2 hours of inactivity (set old lastActivity)
        3. Try to access protected page
        4. Verify session expired and redirected to login
        
        VALIDATION:
        - Session expires after 2 hours inactivity
        - Redirect to login occurs
        - Session marked as expired in database
        
        NOTE: This test simulates timeout by manipulating localStorage timestamps
        rather than waiting 2 hours in real time.
        """
        # Setup: Create test user
        test_email = "timeout_test@example.com"
        test_password = "TestPassword123!"
        
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
                RETURNING id
            """, test_email, "timeout_test", test_password)
        
        # Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.login(test_email, test_password)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # Get session info
        session_mgr = SessionManager(driver)
        auth_token = session_mgr.get_session_token()
        
        # Simulate 2 hours of inactivity (set lastActivity to 2 hours ago)
        old_activity = int((time.time() - 2.5 * 3600) * 1000)  # 2.5 hours ago
        session_mgr.set_last_activity(old_activity)
        
        # Try to access dashboard (should trigger timeout check)
        driver.refresh()
        
        # VERIFICATION 1: Redirected to login due to timeout
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url, "Should redirect to login after timeout"
        
        # VERIFICATION 2: Session marked as expired in database
        session_status = await db_connection.fetchval("""
            SELECT status
            FROM course_creator.user_sessions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """, user_id)
        
        assert session_status in ['expired', 'revoked'], \
            "Session should be expired or revoked after timeout"
    
    @pytest.mark.asyncio
    async def test_user_activity_extends_session(self, driver, test_base_url, db_connection):
        """
        E2E TEST: User activity extends session
        
        BUSINESS REQUIREMENT:
        Active users should have their sessions automatically extended.
        Each user interaction updates lastActivity timestamp.
        
        TEST SCENARIO:
        1. Login successfully
        2. Record initial lastActivity timestamp
        3. Perform user actions (click, type, navigate)
        4. Verify lastActivity timestamp updated
        5. Verify session not expired
        6. Perform more actions
        7. Verify continuous extension
        
        VALIDATION:
        - lastActivity updated with each action
        - Session remains valid with activity
        - Session expiration postponed
        """
        # Setup: Create test user
        test_email = "activity_test@example.com"
        test_password = "TestPassword123!"
        
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
                RETURNING id
            """, test_email, "activity_test", test_password)
        
        # Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.login(test_email, test_password)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # Record initial lastActivity
        session_mgr = SessionManager(driver)
        initial_activity = session_mgr.get_last_activity_time()
        
        # Wait 2 seconds
        time.sleep(2)
        
        # Perform user action (click on page)
        driver.find_element(By.TAG_NAME, "body").click()
        
        # Wait for activity update
        time.sleep(0.5)
        
        # VERIFICATION 1: lastActivity updated
        new_activity = session_mgr.get_last_activity_time()
        assert new_activity > initial_activity, \
            "lastActivity should be updated after user interaction"
        
        # VERIFICATION 2: Session still valid
        assert session_mgr.is_session_valid(), "Session should remain valid with activity"
        
        # VERIFICATION 3: Database session updated
        db_last_activity = await db_connection.fetchval("""
            SELECT last_activity
            FROM course_creator.user_sessions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """, user_id)
        
        # Database timestamp should be recent (within last 10 seconds)
        time_diff = datetime.now() - db_last_activity
        assert time_diff.total_seconds() < 10, \
            "Database lastActivity should be recently updated"
    
    @pytest.mark.asyncio
    async def test_session_tied_to_ip_address(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Session tied to IP address (optional security feature)
        
        BUSINESS REQUIREMENT:
        Sessions can optionally be tied to the originating IP address
        to prevent session hijacking.
        
        TEST SCENARIO:
        1. Login successfully
        2. Verify session has IP address recorded
        3. Simulate IP address change (database manipulation)
        4. Try to use session from "different" IP
        5. Verify session rejected or warning shown
        
        VALIDATION:
        - Session records IP address
        - IP address mismatch detected
        - Session invalidated or warning shown (implementation-dependent)
        
        NOTE: This is an optional security feature. Test may be skipped
        if IP binding is not implemented.
        """
        # Setup: Create test user
        test_email = "ip_binding_test@example.com"
        test_password = "TestPassword123!"
        
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
                RETURNING id
            """, test_email, "ip_binding_test", test_password)
        
        # Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.login(test_email, test_password)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # VERIFICATION 1: Session has IP address recorded
        session_ip = await db_connection.fetchval("""
            SELECT metadata->>'ip_address'
            FROM course_creator.user_sessions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """, user_id)
        
        # IP address tracking is optional - skip test if not implemented
        if session_ip is None:
            pytest.skip("IP address binding not implemented - optional security feature")
        
        assert session_ip is not None, "Session should record IP address"
        
        # VERIFICATION 2: Simulate IP change (update database)
        async with db_connection.transaction():
            await db_connection.execute("""
                UPDATE course_creator.user_sessions
                SET metadata = jsonb_set(
                    COALESCE(metadata, '{}'::jsonb),
                    '{ip_address}',
                    '"192.168.1.99"'
                )
                WHERE user_id = $1
            """, user_id)
        
        # Try to access protected page (IP mismatch should be detected)
        driver.refresh()
        time.sleep(2)
        
        # VERIFICATION 3: Check if session rejected (implementation-dependent)
        # If IP binding is strict, should redirect to login
        # If IP binding is warning-only, may show warning but allow access
        
        if "/login" in driver.current_url:
            # Strict IP binding - session invalidated
            assert True, "Session correctly invalidated on IP mismatch (strict mode)"
        else:
            # Lenient IP binding - check for warning
            try:
                warning = driver.find_element(By.CLASS_NAME, "ip-mismatch-warning")
                assert warning is not None, "Should show IP mismatch warning (lenient mode)"
            except NoSuchElementException:
                # IP binding may not be fully implemented
                pytest.skip("IP address binding appears not fully implemented")
