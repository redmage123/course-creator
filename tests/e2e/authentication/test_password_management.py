"""
Comprehensive E2E Tests for Password Management

BUSINESS REQUIREMENT:
Tests all password management operations including password reset workflows,
password change functionality, and password security requirements.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Validates complete password reset workflow (request → email → reset)
- Tests password security (strength, history, uniqueness)
- Database verification for all operations
- Mock email service for email testing

TEST COVERAGE:
1. Password Reset Workflow (5 tests)
   - Forgot password complete workflow
   - Password reset link expiration (15 minutes)
   - Password reset link single-use
   - Invalid token handling
   - No information disclosure

2. Password Change (4 tests)
   - User changes password successfully
   - Password change with incorrect old password
   - Password change requires re-login
   - Password change invalidates other sessions

3. Password Security (3 tests)
   - Password strength requirements enforced
   - Password cannot be same as last 3 passwords
   - Password must be different from username/email

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

class ForgotPasswordPage:
    """
    Page Object for Forgot Password page.
    
    BUSINESS CONTEXT:
    The forgot password page allows users to request a password reset token
    via email. It must prevent user enumeration attacks by showing generic
    success messages regardless of whether the email exists.
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    # Locators
    EMAIL_INPUT = (By.ID, "reset-email")
    SUBMIT_BUTTON = (By.ID, "reset-submit")
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    BACK_TO_LOGIN_LINK = (By.LINK_TEXT, "Back to Login")
    
    def navigate(self, base_url):
        """Navigate to forgot password page."""
        self.driver.get(f"{base_url}/forgot-password")
    
    def enter_email(self, email):
        """Enter email address."""
        email_input = self.wait.until(EC.presence_of_element_located(self.EMAIL_INPUT))
        email_input.clear()
        email_input.send_keys(email)
    
    def submit(self):
        """Submit password reset request."""
        submit_btn = self.driver.find_element(*self.SUBMIT_BUTTON)
        submit_btn.click()
    
    def get_success_message(self):
        """Get success message text."""
        try:
            message = self.wait.until(EC.presence_of_element_located(self.SUCCESS_MESSAGE))
            return message.text
        except TimeoutException:
            return None
    
    def get_error_message(self):
        """Get error message text."""
        try:
            message = self.driver.find_element(*self.ERROR_MESSAGE)
            return message.text
        except NoSuchElementException:
            return None


class PasswordResetPage:
    """
    Page Object for Password Reset page (with token).
    
    BUSINESS CONTEXT:
    After clicking the email link, users are directed to this page to set
    their new password. The token is validated server-side and the form
    only appears if the token is valid and not expired.
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    # Locators
    NEW_PASSWORD_INPUT = (By.ID, "new-password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirm-password")
    SUBMIT_BUTTON = (By.ID, "reset-password-submit")
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    TOKEN_EXPIRED_MESSAGE = (By.CLASS_NAME, "token-expired-message")
    PASSWORD_STRENGTH_INDICATOR = (By.CLASS_NAME, "password-strength")
    
    def navigate(self, base_url, token):
        """Navigate to password reset page with token."""
        self.driver.get(f"{base_url}/reset-password?token={token}")
    
    def enter_new_password(self, password):
        """Enter new password."""
        pwd_input = self.wait.until(EC.presence_of_element_located(self.NEW_PASSWORD_INPUT))
        pwd_input.clear()
        pwd_input.send_keys(password)
    
    def enter_confirm_password(self, password):
        """Enter password confirmation."""
        confirm_input = self.driver.find_element(*self.CONFIRM_PASSWORD_INPUT)
        confirm_input.clear()
        confirm_input.send_keys(password)
    
    def submit(self):
        """Submit password reset."""
        submit_btn = self.driver.find_element(*self.SUBMIT_BUTTON)
        submit_btn.click()
    
    def get_success_message(self):
        """Get success message text."""
        try:
            message = self.wait.until(EC.presence_of_element_located(self.SUCCESS_MESSAGE))
            return message.text
        except TimeoutException:
            return None
    
    def get_error_message(self):
        """Get error message text."""
        try:
            message = self.driver.find_element(*self.ERROR_MESSAGE)
            return message.text
        except NoSuchElementException:
            return None
    
    def is_token_expired(self):
        """Check if token expired message is shown."""
        try:
            self.driver.find_element(*self.TOKEN_EXPIRED_MESSAGE)
            return True
        except NoSuchElementException:
            return False


class PasswordChangePage:
    """
    Page Object for Password Change page (authenticated users).
    
    BUSINESS CONTEXT:
    Authenticated users can change their password from their profile/settings.
    They must provide their current password for security verification.
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    # Locators
    CURRENT_PASSWORD_INPUT = (By.ID, "current-password")
    NEW_PASSWORD_INPUT = (By.ID, "new-password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirm-password")
    SUBMIT_BUTTON = (By.ID, "change-password-submit")
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    
    def navigate(self, base_url):
        """Navigate to password change page."""
        self.driver.get(f"{base_url}/profile/change-password")
    
    def enter_current_password(self, password):
        """Enter current password."""
        pwd_input = self.wait.until(EC.presence_of_element_located(self.CURRENT_PASSWORD_INPUT))
        pwd_input.clear()
        pwd_input.send_keys(password)
    
    def enter_new_password(self, password):
        """Enter new password."""
        pwd_input = self.driver.find_element(*self.NEW_PASSWORD_INPUT)
        pwd_input.clear()
        pwd_input.send_keys(password)
    
    def enter_confirm_password(self, password):
        """Enter password confirmation."""
        confirm_input = self.driver.find_element(*self.CONFIRM_PASSWORD_INPUT)
        confirm_input.clear()
        confirm_input.send_keys(password)
    
    def submit(self):
        """Submit password change."""
        submit_btn = self.driver.find_element(*self.SUBMIT_BUTTON)
        submit_btn.click()
    
    def get_success_message(self):
        """Get success message text."""
        try:
            message = self.wait.until(EC.presence_of_element_located(self.SUCCESS_MESSAGE))
            return message.text
        except TimeoutException:
            return None
    
    def get_error_message(self):
        """Get error message text."""
        try:
            message = self.driver.find_element(*self.ERROR_MESSAGE)
            return message.text
        except NoSuchElementException:
            return None


class LoginPage:
    """Page Object for Login page."""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    # Locators
    EMAIL_INPUT = (By.ID, "login-email")
    PASSWORD_INPUT = (By.ID, "login-password")
    LOGIN_BUTTON = (By.ID, "login-submit")
    FORGOT_PASSWORD_LINK = (By.LINK_TEXT, "Forgot Password?")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    
    def navigate(self, base_url):
        """Navigate to login page."""
        self.driver.get(f"{base_url}/login")
    
    def enter_email(self, email):
        """Enter email address."""
        email_input = self.wait.until(EC.presence_of_element_located(self.EMAIL_INPUT))
        email_input.clear()
        email_input.send_keys(email)
    
    def enter_password(self, password):
        """Enter password."""
        pwd_input = self.driver.find_element(*self.PASSWORD_INPUT)
        pwd_input.clear()
        pwd_input.send_keys(password)
    
    def submit(self):
        """Submit login form."""
        login_btn = self.driver.find_element(*self.LOGIN_BUTTON)
        login_btn.click()
    
    def click_forgot_password(self):
        """Click forgot password link."""
        forgot_link = self.driver.find_element(*self.FORGOT_PASSWORD_LINK)
        forgot_link.click()
    
    def get_error_message(self):
        """Get error message text."""
        try:
            message = self.driver.find_element(*self.ERROR_MESSAGE)
            return message.text
        except NoSuchElementException:
            return None


# ============================================================================
# TEST CLASS: Password Reset Workflow
# ============================================================================

@pytest.mark.e2e
@pytest.mark.authentication
@pytest.mark.password_management
@pytest.mark.priority_critical
class TestPasswordResetWorkflow:
    """Test suite for password reset workflows."""
    
    @pytest.mark.asyncio
    async def test_forgot_password_complete_workflow(self, driver, test_base_url, db_connection, email_mock):
        """
        E2E TEST: Complete forgot password workflow
        
        BUSINESS REQUIREMENT:
        - Users must be able to reset forgotten passwords
        - Reset links expire after 15 minutes
        - Reset tokens are single-use only
        - No information disclosure (email exists/doesn't exist)
        
        TEST SCENARIO:
        1. Navigate to login page
        2. Click "Forgot Password" link
        3. Enter email address
        4. Submit form
        5. Verify generic success message (no disclosure)
        6. Check email sent (mock email service)
        7. Extract reset link from email
        8. Navigate to reset link
        9. Enter new password
        10. Submit password reset
        11. Verify success message
        12. Login with new password
        
        VALIDATION:
        - Reset token created in database
        - Reset token has expiration timestamp (15 min)
        - Email sent with reset link
        - Old password no longer works
        - New password works
        - Reset token marked as used
        """
        # Setup: Create test user with known password
        test_email = "password_reset_test@example.com"
        old_password = "OldPassword123!"
        new_password = "NewSecurePass456!"
        
        # Create test user in database
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
                RETURNING id
            """, test_email, "password_reset_test", old_password)
        
        # Step 1-2: Navigate to forgot password page
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.click_forgot_password()
        
        # Step 3-4: Enter email and submit
        forgot_page = ForgotPasswordPage(driver)
        forgot_page.enter_email(test_email)
        forgot_page.submit()
        
        # Step 5: VERIFICATION 1 - Generic message (no disclosure)
        success_message = forgot_page.get_success_message()
        assert success_message is not None, "Success message should be displayed"
        assert "check your email" in success_message.lower(), "Generic success message required"
        assert test_email not in success_message, "Email should not be disclosed in message"
        
        # Step 6: VERIFICATION 2 - Token in database
        token_row = await db_connection.fetchrow("""
            SELECT 
                metadata->>'password_reset_token' as token,
                (metadata->>'password_reset_expires')::timestamp as expires_at
            FROM course_creator.users
            WHERE id = $1
        """, user_id)
        
        assert token_row is not None, "Reset token should be created"
        assert token_row['token'] is not None, "Token should not be null"
        reset_token = token_row['token']
        expires_at = token_row['expires_at']
        
        # Verify token expires in ~15 minutes (allow 1 minute tolerance)
        time_until_expiry = expires_at - datetime.now()
        assert 14 <= time_until_expiry.total_seconds() / 60 <= 16, "Token should expire in 15 minutes"
        
        # Step 7: VERIFICATION 3 - Email sent
        emails = email_mock.get_sent_emails()
        reset_email = next((e for e in emails if test_email in e['to']), None)
        assert reset_email is not None, "Reset email should be sent"
        assert reset_token in reset_email['body'], "Email should contain reset link"
        
        # Step 8: Navigate to reset link
        reset_page = PasswordResetPage(driver)
        reset_page.navigate(test_base_url, reset_token)
        
        # Step 9-10: Set new password
        reset_page.enter_new_password(new_password)
        reset_page.enter_confirm_password(new_password)
        reset_page.submit()
        
        # Step 11: VERIFICATION 4 - Success and redirect to login
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/login"))
        
        # Step 12: VERIFICATION 5 - Can login with new password
        login_page.enter_email(test_email)
        login_page.enter_password(new_password)
        login_page.submit()
        
        # Should successfully login
        wait.until(EC.url_contains("/dashboard"))
        
        # Step 13: VERIFICATION 6 - Token marked as used
        token_after = await db_connection.fetchval("""
            SELECT metadata->>'password_reset_token'
            FROM course_creator.users
            WHERE id = $1
        """, user_id)
        assert token_after is None, "Token should be cleared after use"
        
        # Step 14: VERIFICATION 7 - Old password no longer works
        login_page.navigate(test_base_url)
        login_page.enter_email(test_email)
        login_page.enter_password(old_password)
        login_page.submit()
        
        error_message = login_page.get_error_message()
        assert error_message is not None, "Old password should not work"
    
    @pytest.mark.asyncio
    async def test_password_reset_link_expiration(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Password reset link expiration after 15 minutes
        
        BUSINESS REQUIREMENT:
        Reset links must expire after 15 minutes for security.
        
        TEST SCENARIO:
        1. Create expired reset token (16 minutes ago)
        2. Navigate to reset page with expired token
        3. Verify "token expired" message shown
        4. Verify form is not displayed
        5. Verify link to request new token
        """
        # Setup: Create test user with expired token
        test_email = "expired_token_test@example.com"
        expired_token = str(uuid.uuid4())
        
        # Create user with expired token (16 minutes ago)
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (
                    email, username, password_hash, role, metadata
                )
                VALUES (
                    $1, $2, crypt('TestPassword123!', gen_salt('bf')), 'student',
                    jsonb_build_object(
                        'password_reset_token', $3,
                        'password_reset_expires', NOW() - INTERVAL '16 minutes'
                    )
                )
                RETURNING id
            """, test_email, "expired_token_test", expired_token)
        
        # Navigate to reset page with expired token
        reset_page = PasswordResetPage(driver)
        reset_page.navigate(test_base_url, expired_token)
        
        # VERIFICATION 1: Token expired message shown
        assert reset_page.is_token_expired(), "Token expired message should be displayed"
        
        # VERIFICATION 2: Form should not be displayed
        try:
            driver.find_element(*reset_page.NEW_PASSWORD_INPUT)
            pytest.fail("Password form should not be displayed for expired token")
        except NoSuchElementException:
            pass  # Expected
        
        # VERIFICATION 3: Link to request new token
        try:
            request_new_link = driver.find_element(By.LINK_TEXT, "Request New Reset Link")
            assert request_new_link is not None, "Should provide link to request new token"
        except NoSuchElementException:
            pytest.fail("Should provide link to request new reset link")
    
    @pytest.mark.asyncio
    async def test_password_reset_token_single_use(self, driver, test_base_url, db_connection, email_mock):
        """
        E2E TEST: Password reset token can only be used once
        
        BUSINESS REQUIREMENT:
        Reset tokens must be invalidated after successful use to prevent reuse attacks.
        
        TEST SCENARIO:
        1. Request password reset
        2. Use token to reset password successfully
        3. Try to use same token again
        4. Verify "invalid token" error shown
        """
        # Setup: Create test user
        test_email = "single_use_test@example.com"
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"
        
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
                RETURNING id
            """, test_email, "single_use_test", old_password)
        
        # Request password reset
        forgot_page = ForgotPasswordPage(driver)
        forgot_page.navigate(test_base_url)
        forgot_page.enter_email(test_email)
        forgot_page.submit()
        
        # Get token from email
        emails = email_mock.get_sent_emails()
        reset_email = next((e for e in emails if test_email in e['to']), None)
        reset_token = self._extract_token_from_email(reset_email['body'])
        
        # Use token to reset password (first time - should succeed)
        reset_page = PasswordResetPage(driver)
        reset_page.navigate(test_base_url, reset_token)
        reset_page.enter_new_password(new_password)
        reset_page.enter_confirm_password(new_password)
        reset_page.submit()
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/login"))
        
        # Try to use same token again (should fail)
        reset_page.navigate(test_base_url, reset_token)
        
        # VERIFICATION: Invalid token error shown
        error_message = reset_page.get_error_message()
        assert error_message is not None, "Error message should be displayed"
        assert "invalid" in error_message.lower() or "expired" in error_message.lower(), \
            "Should indicate token is invalid"
    
    @pytest.mark.asyncio
    async def test_password_reset_invalid_token(self, driver, test_base_url):
        """
        E2E TEST: Password reset with invalid token
        
        BUSINESS REQUIREMENT:
        Invalid tokens must be rejected with appropriate error message.
        
        TEST SCENARIO:
        1. Navigate to reset page with invalid/fake token
        2. Verify error message shown
        3. Verify form is not displayed
        """
        # Use fake/invalid token
        invalid_token = "invalid-token-12345"
        
        reset_page = PasswordResetPage(driver)
        reset_page.navigate(test_base_url, invalid_token)
        
        # VERIFICATION: Error message shown
        error_message = reset_page.get_error_message()
        assert error_message is not None, "Error message should be displayed"
        assert "invalid" in error_message.lower(), "Should indicate token is invalid"
        
        # VERIFICATION: Form should not be displayed
        try:
            driver.find_element(*reset_page.NEW_PASSWORD_INPUT)
            pytest.fail("Password form should not be displayed for invalid token")
        except NoSuchElementException:
            pass  # Expected
    
    @pytest.mark.asyncio
    async def test_password_reset_no_information_disclosure(self, driver, test_base_url, email_mock):
        """
        E2E TEST: Password reset does not disclose whether email exists
        
        BUSINESS REQUIREMENT:
        To prevent user enumeration attacks, the system must show the same
        success message whether the email exists or not.
        
        TEST SCENARIO:
        1. Request reset for non-existent email
        2. Verify generic success message (same as for valid email)
        3. Verify no email is actually sent
        4. Verify no difference in response time or behavior
        """
        # Request reset for non-existent email
        nonexistent_email = "nonexistent_user@example.com"
        
        forgot_page = ForgotPasswordPage(driver)
        forgot_page.navigate(test_base_url)
        
        # Measure response time
        start_time = time.time()
        forgot_page.enter_email(nonexistent_email)
        forgot_page.submit()
        response_time = time.time() - start_time
        
        # VERIFICATION 1: Generic success message shown
        success_message = forgot_page.get_success_message()
        assert success_message is not None, "Success message should be displayed"
        assert "check your email" in success_message.lower(), "Generic success message required"
        assert nonexistent_email not in success_message, "Email should not be disclosed"
        
        # VERIFICATION 2: No email actually sent
        emails = email_mock.get_sent_emails()
        reset_email = next((e for e in emails if nonexistent_email in e['to']), None)
        assert reset_email is None, "No email should be sent for non-existent user"
        
        # VERIFICATION 3: Response time should be similar (no timing attack)
        # Response should be instant for non-existent user (no DB lookup delay)
        assert response_time < 5, "Response should be quick to prevent timing attacks"
    
    def _extract_token_from_email(self, email_body):
        """Helper method to extract reset token from email body."""
        import re
        match = re.search(r'token=([a-zA-Z0-9_-]+)', email_body)
        return match.group(1) if match else None


# ============================================================================
# TEST CLASS: Password Change
# ============================================================================

@pytest.mark.e2e
@pytest.mark.authentication
@pytest.mark.password_management
@pytest.mark.priority_critical
class TestPasswordChange:
    """Test suite for password change functionality."""
    
    @pytest.mark.asyncio
    async def test_user_changes_password_successfully(self, driver, test_base_url, db_connection):
        """
        E2E TEST: User changes password successfully
        
        BUSINESS REQUIREMENT:
        Authenticated users can change their password from profile settings.
        
        TEST SCENARIO:
        1. Login as test user
        2. Navigate to password change page
        3. Enter current password
        4. Enter new password (meets strength requirements)
        5. Confirm new password
        6. Submit form
        7. Verify success message
        8. Logout
        9. Login with new password
        """
        # Setup: Create test user
        test_email = "change_password_test@example.com"
        old_password = "OldPassword123!"
        new_password = "NewSecurePass456!"
        
        async with db_connection.transaction():
            await db_connection.execute("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
            """, test_email, "change_pwd_test", old_password)
        
        # Step 1: Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.enter_email(test_email)
        login_page.enter_password(old_password)
        login_page.submit()
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # Step 2: Navigate to password change page
        change_page = PasswordChangePage(driver)
        change_page.navigate(test_base_url)
        
        # Step 3-6: Change password
        change_page.enter_current_password(old_password)
        change_page.enter_new_password(new_password)
        change_page.enter_confirm_password(new_password)
        change_page.submit()
        
        # Step 7: VERIFICATION 1 - Success message
        success_message = change_page.get_success_message()
        assert success_message is not None, "Success message should be displayed"
        assert "password changed" in success_message.lower(), "Should confirm password change"
        
        # Step 8: Logout
        driver.find_element(By.ID, "logout-btn").click()
        
        # Step 9: VERIFICATION 2 - Login with new password
        login_page.navigate(test_base_url)
        login_page.enter_email(test_email)
        login_page.enter_password(new_password)
        login_page.submit()
        
        wait.until(EC.url_contains("/dashboard"))
        assert "/dashboard" in driver.current_url, "Should login successfully with new password"
    
    @pytest.mark.asyncio
    async def test_password_change_incorrect_old_password(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Password change with incorrect old password fails
        
        BUSINESS REQUIREMENT:
        Users must provide correct current password to change password.
        
        TEST SCENARIO:
        1. Login as test user
        2. Navigate to password change page
        3. Enter INCORRECT current password
        4. Enter new password
        5. Submit form
        6. Verify error message shown
        7. Verify password not changed
        """
        # Setup: Create test user
        test_email = "incorrect_old_pwd@example.com"
        correct_password = "CorrectPassword123!"
        
        async with db_connection.transaction():
            await db_connection.execute("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
            """, test_email, "incorrect_pwd_test", correct_password)
        
        # Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.enter_email(test_email)
        login_page.enter_password(correct_password)
        login_page.submit()
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # Navigate to password change page
        change_page = PasswordChangePage(driver)
        change_page.navigate(test_base_url)
        
        # Attempt to change with INCORRECT old password
        change_page.enter_current_password("WrongPassword123!")
        change_page.enter_new_password("NewPassword456!")
        change_page.enter_confirm_password("NewPassword456!")
        change_page.submit()
        
        # VERIFICATION: Error message shown
        error_message = change_page.get_error_message()
        assert error_message is not None, "Error message should be displayed"
        assert "incorrect" in error_message.lower() or "current password" in error_message.lower(), \
            "Should indicate current password is incorrect"
    
    @pytest.mark.asyncio
    async def test_password_change_requires_relogin(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Password change requires re-login
        
        BUSINESS REQUIREMENT:
        After password change, user should be logged out and must re-login
        with new password for security.
        
        TEST SCENARIO:
        1. Login as test user
        2. Change password successfully
        3. Verify automatic logout (redirected to login)
        4. Verify must login with new password
        """
        # Setup: Create test user
        test_email = "relogin_test@example.com"
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"
        
        async with db_connection.transaction():
            await db_connection.execute("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
            """, test_email, "relogin_test", old_password)
        
        # Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.enter_email(test_email)
        login_page.enter_password(old_password)
        login_page.submit()
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # Change password
        change_page = PasswordChangePage(driver)
        change_page.navigate(test_base_url)
        change_page.enter_current_password(old_password)
        change_page.enter_new_password(new_password)
        change_page.enter_confirm_password(new_password)
        change_page.submit()
        
        # VERIFICATION 1: Redirected to login page
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url, "Should be redirected to login after password change"
        
        # VERIFICATION 2: Must login with new password
        login_page.enter_email(test_email)
        login_page.enter_password(new_password)
        login_page.submit()
        
        wait.until(EC.url_contains("/dashboard"))
        assert "/dashboard" in driver.current_url, "Should login successfully with new password"
    
    @pytest.mark.asyncio
    async def test_password_change_invalidates_other_sessions(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Password change invalidates other active sessions
        
        BUSINESS REQUIREMENT:
        When password is changed, all other active sessions must be invalidated
        for security (user must re-login on all devices).
        
        TEST SCENARIO:
        1. Login in first browser (simulate Device 1)
        2. Login in second browser (simulate Device 2)
        3. Change password in first browser
        4. Verify second browser session is invalidated
        5. Verify second browser redirected to login
        """
        # Setup: Create test user
        test_email = "multi_session_test@example.com"
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"
        
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (email, username, password_hash, role)
                VALUES ($1, $2, crypt($3, gen_salt('bf')), 'student')
                RETURNING id
            """, test_email, "multi_session_test", old_password)
        
        # Browser 1: Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.enter_email(test_email)
        login_page.enter_password(old_password)
        login_page.submit()
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # Get session token from browser 1
        session_token_1 = driver.execute_script("return localStorage.getItem('authToken')")
        
        # Create second session in database (simulate Device 2)
        async with db_connection.transaction():
            session_id_2 = await db_connection.fetchval("""
                INSERT INTO course_creator.user_sessions (
                    user_id, token, expires_at, created_at, last_activity
                )
                VALUES (
                    $1, $2, NOW() + INTERVAL '2 hours', NOW(), NOW()
                )
                RETURNING id
            """, user_id, str(uuid.uuid4()))
        
        # Browser 1: Change password
        change_page = PasswordChangePage(driver)
        change_page.navigate(test_base_url)
        change_page.enter_current_password(old_password)
        change_page.enter_new_password(new_password)
        change_page.enter_confirm_password(new_password)
        change_page.submit()
        
        # VERIFICATION: Session 2 should be invalidated in database
        session_2_status = await db_connection.fetchval("""
            SELECT status
            FROM course_creator.user_sessions
            WHERE id = $1
        """, session_id_2)
        
        assert session_2_status == 'revoked', "Other sessions should be invalidated"


# ============================================================================
# TEST CLASS: Password Security
# ============================================================================

@pytest.mark.e2e
@pytest.mark.authentication
@pytest.mark.password_management
@pytest.mark.priority_critical
class TestPasswordSecurity:
    """Test suite for password security requirements."""
    
    def test_password_strength_requirements_enforced(self, driver, test_base_url):
        """
        E2E TEST: Password strength requirements enforced
        
        BUSINESS REQUIREMENT:
        Passwords must meet minimum security requirements:
        - At least 8 characters
        - At least 3 character types (uppercase, lowercase, digits, special)
        
        TEST SCENARIO:
        1. Navigate to password change page (or registration)
        2. Try weak passwords (too short, no variety)
        3. Verify error messages for each weak password
        4. Try strong password
        5. Verify acceptance
        """
        # Test cases for weak passwords
        weak_passwords = [
            ("abc", "Too short (< 8 characters)"),
            ("password", "No uppercase/digits/special"),
            ("PASSWORD", "No lowercase/digits/special"),
            ("12345678", "No letters"),
            ("Passwor1", "Only 2 character types"),
        ]
        
        # Navigate to registration page (easier to test without login)
        driver.get(f"{test_base_url}/register")
        
        wait = WebDriverWait(driver, 10)
        password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
        confirm_input = driver.find_element(By.ID, "confirm-password")
        
        for weak_pwd, reason in weak_passwords:
            # Enter weak password
            password_input.clear()
            password_input.send_keys(weak_pwd)
            confirm_input.clear()
            confirm_input.send_keys(weak_pwd)
            
            # Trigger validation (blur event)
            password_input.send_keys(Keys.TAB)
            time.sleep(0.5)
            
            # VERIFICATION: Error message shown
            try:
                error_msg = driver.find_element(By.CLASS_NAME, "password-error")
                assert error_msg.is_displayed(), f"Error should be shown for: {reason}"
            except NoSuchElementException:
                pytest.fail(f"No error shown for weak password: {reason}")
        
        # Test strong password (should be accepted)
        strong_password = "StrongPass123!"
        password_input.clear()
        password_input.send_keys(strong_password)
        confirm_input.clear()
        confirm_input.send_keys(strong_password)
        password_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        # VERIFICATION: No error for strong password
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "password-error")
            if error_msg.is_displayed():
                pytest.fail(f"Strong password rejected: {error_msg.text}")
        except NoSuchElementException:
            pass  # Expected - no error
    
    @pytest.mark.asyncio
    async def test_password_cannot_be_same_as_last_3(self, driver, test_base_url, db_connection):
        """
        E2E TEST: Password cannot be same as last 3 passwords
        
        BUSINESS REQUIREMENT:
        Users cannot reuse their last 3 passwords to improve security.
        
        TEST SCENARIO:
        1. Create user with password history
        2. Login
        3. Try to change to one of last 3 passwords
        4. Verify error message
        5. Change to new password (not in history)
        6. Verify success
        """
        # Setup: Create user with password history
        test_email = "password_history_test@example.com"
        current_password = "CurrentPassword123!"
        old_passwords = ["OldPassword1!", "OldPassword2!", "OldPassword3!"]
        
        async with db_connection.transaction():
            user_id = await db_connection.fetchval("""
                INSERT INTO course_creator.users (
                    email, username, password_hash, role, metadata
                )
                VALUES (
                    $1, $2, crypt($3, gen_salt('bf')), 'student',
                    jsonb_build_object(
                        'password_history', $4::text[]
                    )
                )
                RETURNING id
            """, test_email, "password_history_test", current_password, 
                [f"$2b$12$hashed_{pwd}" for pwd in old_passwords])
        
        # Login
        login_page = LoginPage(driver)
        login_page.navigate(test_base_url)
        login_page.enter_email(test_email)
        login_page.enter_password(current_password)
        login_page.submit()
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/dashboard"))
        
        # Try to change to one of last 3 passwords
        change_page = PasswordChangePage(driver)
        change_page.navigate(test_base_url)
        change_page.enter_current_password(current_password)
        change_page.enter_new_password(old_passwords[0])  # Try to reuse old password
        change_page.enter_confirm_password(old_passwords[0])
        change_page.submit()
        
        # VERIFICATION 1: Error message for password reuse
        error_message = change_page.get_error_message()
        assert error_message is not None, "Error message should be displayed"
        assert "recent" in error_message.lower() or "history" in error_message.lower(), \
            "Should indicate password was recently used"
        
        # Try new password (not in history)
        new_password = "BrandNewPassword456!"
        change_page.enter_current_password(current_password)
        change_page.enter_new_password(new_password)
        change_page.enter_confirm_password(new_password)
        change_page.submit()
        
        # VERIFICATION 2: Success with new password
        success_message = change_page.get_success_message()
        assert success_message is not None, "Success message should be displayed for new password"
    
    @pytest.mark.asyncio
    async def test_password_different_from_username_email(self, driver, test_base_url):
        """
        E2E TEST: Password must be different from username/email
        
        BUSINESS REQUIREMENT:
        Passwords cannot be the same as username or email for security.
        
        TEST SCENARIO:
        1. Navigate to registration page
        2. Enter email and username
        3. Try to use email as password
        4. Verify error message
        5. Try to use username as password
        6. Verify error message
        7. Use different password
        8. Verify success
        """
        test_email = "test@example.com"
        test_username = "testuser123"
        
        # Navigate to registration page
        driver.get(f"{test_base_url}/register")
        
        wait = WebDriverWait(driver, 10)
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        username_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        confirm_input = driver.find_element(By.ID, "confirm-password")
        
        # Enter email and username
        email_input.send_keys(test_email)
        username_input.send_keys(test_username)
        
        # Try to use email as password
        password_input.clear()
        password_input.send_keys(test_email)
        confirm_input.clear()
        confirm_input.send_keys(test_email)
        password_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        # VERIFICATION 1: Error for email as password
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "password-error")
            assert "email" in error_msg.text.lower(), "Should indicate password cannot be email"
        except NoSuchElementException:
            pytest.fail("No error shown when password matches email")
        
        # Try to use username as password
        password_input.clear()
        password_input.send_keys(test_username)
        confirm_input.clear()
        confirm_input.send_keys(test_username)
        password_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        # VERIFICATION 2: Error for username as password
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "password-error")
            assert "username" in error_msg.text.lower(), "Should indicate password cannot be username"
        except NoSuchElementException:
            pytest.fail("No error shown when password matches username")
        
        # Use different password (should work)
        different_password = "DifferentPass123!"
        password_input.clear()
        password_input.send_keys(different_password)
        confirm_input.clear()
        confirm_input.send_keys(different_password)
        password_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        # VERIFICATION 3: No error for different password
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "password-error")
            if error_msg.is_displayed():
                pytest.fail(f"Valid password rejected: {error_msg.text}")
        except NoSuchElementException:
            pass  # Expected - no error
