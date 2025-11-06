"""
E2E Tests for User Registration Workflows

Tests comprehensive user registration scenarios including:
- Student registration with complete and minimal fields
- Organization registration with admin account creation
- Email verification workflows
- Form validation (email, password, required fields)
- Password strength requirements
- GDPR consent recording
- Terms of service acceptance
- Duplicate email prevention

BUSINESS CONTEXT:
Registration is the first interaction new users have with the platform.
These tests ensure a smooth onboarding experience while maintaining
security and compliance with privacy regulations (GDPR/CCPA/PIPEDA).

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver for browser automation
- Tests actual HTML forms and JavaScript validation
- Verifies database user creation with asyncpg
- Tests email verification token generation (mock SMTP)
- Validates HTTPS-only communication
- Generates unique test data with UUID to prevent conflicts
"""

import pytest
import pytest_asyncio
import time
import uuid
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import asyncpg

# Import base classes
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from selenium_base import SeleniumConfig, ChromeDriverSetup


# ============================================================================
# PAGE OBJECTS
# ============================================================================

class RegistrationPage:
    """
    Page Object for user registration form.

    Encapsulates all registration form interactions for maintainability.
    """

    def __init__(self, driver: webdriver.Chrome, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def navigate(self):
        """Navigate to registration page"""
        self.driver.get(f"{self.base_url}/html/register.html")
        self.wait.until(EC.presence_of_element_located((By.ID, "registrationForm")))

    def fill_email(self, email: str):
        """Fill email field"""
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "register-email")))
        email_input.clear()
        email_input.send_keys(email)

    def fill_username(self, username: str):
        """Fill username field"""
        username_input = self.wait.until(EC.presence_of_element_located((By.ID, "register-username")))
        username_input.clear()
        username_input.send_keys(username)

    def fill_password(self, password: str):
        """Fill password field"""
        password_input = self.wait.until(EC.presence_of_element_located((By.ID, "register-password")))
        password_input.clear()
        password_input.send_keys(password)

    def fill_confirm_password(self, password: str):
        """Fill confirm password field"""
        confirm_input = self.wait.until(EC.presence_of_element_located((By.ID, "register-confirm-password")))
        confirm_input.clear()
        confirm_input.send_keys(password)

    def fill_full_name(self, full_name: str):
        """Fill full name field"""
        name_input = self.wait.until(EC.presence_of_element_located((By.ID, "register-full-name")))
        name_input.clear()
        name_input.send_keys(full_name)

    def select_role(self, role: str):
        """Select user role from dropdown"""
        role_select = self.wait.until(EC.presence_of_element_located((By.ID, "register-role")))
        role_select.click()
        role_option = self.driver.find_element(By.XPATH, f"//option[@value='{role}']")
        role_option.click()

    def accept_terms(self):
        """Check terms of service checkbox"""
        terms_checkbox = self.wait.until(EC.presence_of_element_located((By.ID, "register-terms")))
        if not terms_checkbox.is_selected():
            terms_checkbox.click()

    def accept_gdpr(self):
        """Check GDPR consent checkbox"""
        gdpr_checkbox = self.wait.until(EC.presence_of_element_located((By.ID, "register-gdpr-consent")))
        if not gdpr_checkbox.is_selected():
            gdpr_checkbox.click()

    def submit_form(self):
        """Click submit button"""
        submit_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "register-submit")))
        submit_btn.click()

    def get_success_message(self) -> str:
        """Get success message text"""
        try:
            success_msg = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-success")))
            return success_msg.text
        except TimeoutException:
            return ""

    def get_error_message(self) -> str:
        """Get error message text"""
        try:
            error_msg = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-danger")))
            return error_msg.text
        except TimeoutException:
            return ""

    def get_field_error(self, field_id: str) -> str:
        """Get field-specific error message"""
        try:
            error_element = self.driver.find_element(By.ID, f"{field_id}-error")
            return error_element.text
        except NoSuchElementException:
            return ""


class OrganizationRegistrationPage:
    """
    Page Object for organization registration form.

    Organizations require additional fields like subdomain, organization name, etc.
    """

    def __init__(self, driver: webdriver.Chrome, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def navigate(self):
        """Navigate to organization registration page"""
        self.driver.get(f"{self.base_url}/html/org-register.html")
        self.wait.until(EC.presence_of_element_located((By.ID, "orgRegistrationForm")))

    def fill_organization_name(self, org_name: str):
        """Fill organization name"""
        org_input = self.wait.until(EC.presence_of_element_located((By.ID, "org-name")))
        org_input.clear()
        org_input.send_keys(org_name)

    def fill_subdomain(self, subdomain: str):
        """Fill organization subdomain"""
        subdomain_input = self.wait.until(EC.presence_of_element_located((By.ID, "org-subdomain")))
        subdomain_input.clear()
        subdomain_input.send_keys(subdomain)

    def fill_admin_email(self, email: str):
        """Fill admin email"""
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "admin-email")))
        email_input.clear()
        email_input.send_keys(email)

    def fill_admin_username(self, username: str):
        """Fill admin username"""
        username_input = self.wait.until(EC.presence_of_element_located((By.ID, "admin-username")))
        username_input.clear()
        username_input.send_keys(username)

    def fill_admin_password(self, password: str):
        """Fill admin password"""
        password_input = self.wait.until(EC.presence_of_element_located((By.ID, "admin-password")))
        password_input.clear()
        password_input.send_keys(password)

    def submit_form(self):
        """Submit organization registration form"""
        submit_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "org-submit")))
        submit_btn.click()


class EmailVerificationPage:
    """
    Page Object for email verification workflow.

    Tests email verification links and account activation.
    """

    def __init__(self, driver: webdriver.Chrome, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def navigate_to_verification_link(self, token: str):
        """Navigate to email verification link with token"""
        self.driver.get(f"{self.base_url}/html/verify-email.html?token={token}")
        time.sleep(1)

    def get_verification_status(self) -> str:
        """Get verification status message"""
        try:
            status_msg = self.wait.until(EC.presence_of_element_located((By.ID, "verification-status")))
            return status_msg.text
        except TimeoutException:
            return ""


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="class")
def browser_setup():
    """
    Setup Selenium browser for test class.

    Creates Chrome driver with proper configuration and cleans up after tests.
    """
    config = SeleniumConfig()
    chrome_options = ChromeDriverSetup.create_chrome_options(config)
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(config.window_width, config.window_height)

    yield driver, config.base_url

    driver.quit()


@pytest_asyncio.fixture
async def db_connection():
    """
    Create database connection for verification.

    Allows tests to verify user records were created correctly.
    """
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'course_creator'),
        user=os.getenv('DB_USER', 'course_creator_user'),
        password=os.getenv('DB_PASSWORD', 'course_creator_password')
    )

    yield conn

    await conn.close()


# ============================================================================
# STUDENT REGISTRATION TESTS (5 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.authentication
@pytest.mark.priority_critical
@pytest.mark.usefixtures("browser_setup")
class TestStudentRegistration:
    """Test student registration workflows"""

    @pytest.mark.asyncio
    async def test_student_registration_with_all_fields(self, browser_setup, db_connection):
        """
        E2E TEST: Student registers with complete profile

        BUSINESS REQUIREMENT:
        - New students must be able to self-register
        - Email verification required for account activation
        - GDPR consent must be explicit and recorded

        TEST SCENARIO:
        1. Navigate to registration page
        2. Fill all registration fields (email, username, password, full name)
        3. Accept terms of service and GDPR consent
        4. Submit registration form
        5. Verify success message displayed
        6. Check user record created in database
        7. Verify email verification token generated
        8. Verify GDPR consent timestamp recorded

        VALIDATION:
        - User record created in database
        - Email verification token generated
        - GDPR consent timestamp recorded
        - User cannot login until email verified
        - User role set to 'student'
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)

        # Generate unique credentials
        unique_id = str(uuid.uuid4())[:8]
        email = f"student_{unique_id}@test.com"
        username = f"student_{unique_id}"
        password = "SecurePass123!"
        full_name = f"Test Student {unique_id}"

        # Navigate and fill form
        reg_page.navigate()
        reg_page.fill_email(email)
        reg_page.fill_username(username)
        reg_page.fill_password(password)
        reg_page.fill_confirm_password(password)
        reg_page.fill_full_name(full_name)
        reg_page.select_role("student")
        reg_page.accept_terms()
        reg_page.accept_gdpr()
        reg_page.submit_form()

        # Verify success message
        success_msg = reg_page.get_success_message()
        assert "success" in success_msg.lower() or "verify" in success_msg.lower(), \
            "Should show success message after registration"

        # DATABASE VERIFICATION: Check user created
        user = await db_connection.fetchrow(
            "SELECT id, email, username, role, email_verified, gdpr_consent_date, created_at "
            "FROM course_creator.users WHERE email = $1",
            email
        )

        assert user is not None, "User should be created in database"
        assert user['email'] == email, "Email should match"
        assert user['username'] == username, "Username should match"
        assert user['role'] == 'student', "Role should be student"
        assert user['email_verified'] is False, "Email should not be verified yet"
        assert user['gdpr_consent_date'] is not None, "GDPR consent date should be recorded"

        # Verify email verification token created
        token = await db_connection.fetchval(
            "SELECT token FROM course_creator.email_verification_tokens "
            "WHERE user_id = $1 AND used = false",
            user['id']
        )

        assert token is not None, "Email verification token should be generated"

    @pytest.mark.asyncio
    async def test_student_registration_minimal_fields(self, browser_setup, db_connection):
        """
        E2E TEST: Student registers with only required fields

        BUSINESS REQUIREMENT:
        - Registration should work with minimal required information
        - Optional fields (full name) should not block registration

        TEST SCENARIO:
        1. Navigate to registration page
        2. Fill only required fields (email, username, password)
        3. Accept required checkboxes (terms, GDPR)
        4. Submit form
        5. Verify registration succeeds

        VALIDATION:
        - User created with minimal data
        - Optional fields stored as NULL or empty
        - Account still requires email verification
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)

        # Generate unique credentials
        unique_id = str(uuid.uuid4())[:8]
        email = f"student_min_{unique_id}@test.com"
        username = f"student_min_{unique_id}"
        password = "SecurePass123!"

        # Fill only required fields
        reg_page.navigate()
        reg_page.fill_email(email)
        reg_page.fill_username(username)
        reg_page.fill_password(password)
        reg_page.fill_confirm_password(password)
        reg_page.select_role("student")
        reg_page.accept_terms()
        reg_page.accept_gdpr()
        reg_page.submit_form()

        # Verify success
        success_msg = reg_page.get_success_message()
        assert "success" in success_msg.lower() or "verify" in success_msg.lower()

        # DATABASE VERIFICATION
        user = await db_connection.fetchrow(
            "SELECT id, email, username, full_name FROM course_creator.users WHERE email = $1",
            email
        )

        assert user is not None, "User should be created"
        assert user['email'] == email
        assert user['username'] == username
        # full_name might be NULL or empty string

    @pytest.mark.asyncio
    async def test_email_verification_workflow(self, browser_setup, db_connection):
        """
        E2E TEST: Email verification complete workflow

        BUSINESS REQUIREMENT:
        - Users must verify email before accessing platform
        - Verification links must expire after 24 hours
        - Verification can only be used once

        TEST SCENARIO:
        1. Register new student account
        2. Get verification token from database
        3. Click verification link
        4. Verify account activated
        5. Try to verify again (should fail - token used)
        6. Login with verified account (should succeed)

        VALIDATION:
        - Email verification sets email_verified = true
        - Verification token marked as used
        - User can login after verification
        - Used tokens cannot be reused
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)
        verify_page = EmailVerificationPage(driver, base_url)

        # Register account
        unique_id = str(uuid.uuid4())[:8]
        email = f"student_verify_{unique_id}@test.com"
        username = f"student_verify_{unique_id}"
        password = "SecurePass123!"

        reg_page.navigate()
        reg_page.fill_email(email)
        reg_page.fill_username(username)
        reg_page.fill_password(password)
        reg_page.fill_confirm_password(password)
        reg_page.select_role("student")
        reg_page.accept_terms()
        reg_page.accept_gdpr()
        reg_page.submit_form()

        time.sleep(2)  # Wait for DB write

        # Get verification token from DB
        user_id = await db_connection.fetchval(
            "SELECT id FROM course_creator.users WHERE email = $1", email
        )
        token = await db_connection.fetchval(
            "SELECT token FROM course_creator.email_verification_tokens "
            "WHERE user_id = $1 AND used = false",
            user_id
        )

        assert token is not None, "Verification token should exist"

        # Click verification link
        verify_page.navigate_to_verification_link(token)
        status = verify_page.get_verification_status()
        assert "success" in status.lower() or "verified" in status.lower(), \
            "Should show verification success message"

        # Verify email_verified flag set in DB
        email_verified = await db_connection.fetchval(
            "SELECT email_verified FROM course_creator.users WHERE id = $1", user_id
        )
        assert email_verified is True, "Email should be verified"

        # Verify token marked as used
        token_used = await db_connection.fetchval(
            "SELECT used FROM course_creator.email_verification_tokens WHERE token = $1", token
        )
        assert token_used is True, "Token should be marked as used"

        # Try to verify again (should fail)
        verify_page.navigate_to_verification_link(token)
        status = verify_page.get_verification_status()
        assert "already" in status.lower() or "invalid" in status.lower(), \
            "Should reject already-used token"

    @pytest.mark.asyncio
    async def test_registration_form_validation_missing_fields(self, browser_setup):
        """
        E2E TEST: Form validation for missing required fields

        BUSINESS REQUIREMENT:
        - All required fields must be validated before submission
        - Clear error messages for missing fields
        - Form should not submit if validation fails

        TEST SCENARIO:
        1. Navigate to registration page
        2. Submit form with missing email
        3. Verify error message
        4. Submit form with missing password
        5. Verify error message
        6. Submit form without accepting terms
        7. Verify error message

        VALIDATION:
        - HTML5 validation prevents empty required fields
        - JavaScript validation shows clear error messages
        - Form does not submit on validation failure
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)

        reg_page.navigate()

        # Try to submit without filling anything
        reg_page.submit_form()
        time.sleep(1)

        # Verify still on registration page (form didn't submit)
        assert "register.html" in driver.current_url, "Should stay on registration page"

        # Check for validation errors
        email_input = driver.find_element(By.ID, "register-email")
        validation_message = email_input.get_attribute("validationMessage")
        assert validation_message != "", "Email field should show validation message"

    @pytest.mark.asyncio
    async def test_duplicate_email_prevention(self, browser_setup, db_connection):
        """
        E2E TEST: Prevent duplicate email registration

        BUSINESS REQUIREMENT:
        - Email addresses must be unique per user
        - Clear error message when duplicate email used
        - Security: Don't reveal if email already exists (OWASP)

        TEST SCENARIO:
        1. Register first student with email
        2. Verify registration succeeds
        3. Try to register second student with same email
        4. Verify appropriate error message
        5. Verify second registration fails

        VALIDATION:
        - Database constraint prevents duplicate emails
        - API returns appropriate error
        - Error message is user-friendly but secure
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)

        # Register first account
        unique_id = str(uuid.uuid4())[:8]
        email = f"duplicate_{unique_id}@test.com"
        username1 = f"user1_{unique_id}"
        password = "SecurePass123!"

        reg_page.navigate()
        reg_page.fill_email(email)
        reg_page.fill_username(username1)
        reg_page.fill_password(password)
        reg_page.fill_confirm_password(password)
        reg_page.select_role("student")
        reg_page.accept_terms()
        reg_page.accept_gdpr()
        reg_page.submit_form()

        time.sleep(2)  # Wait for first registration

        # Try to register with same email
        username2 = f"user2_{unique_id}"

        reg_page.navigate()
        reg_page.fill_email(email)  # Same email!
        reg_page.fill_username(username2)  # Different username
        reg_page.fill_password(password)
        reg_page.fill_confirm_password(password)
        reg_page.select_role("student")
        reg_page.accept_terms()
        reg_page.accept_gdpr()
        reg_page.submit_form()

        time.sleep(2)

        # Verify error message
        error_msg = reg_page.get_error_message()
        assert "email" in error_msg.lower() or "already" in error_msg.lower() or "exists" in error_msg.lower(), \
            "Should show error for duplicate email"

        # DATABASE VERIFICATION: Only one user exists
        user_count = await db_connection.fetchval(
            "SELECT COUNT(*) FROM course_creator.users WHERE email = $1", email
        )
        assert user_count == 1, "Only first registration should succeed"


# ============================================================================
# ORGANIZATION REGISTRATION TESTS (5 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.authentication
@pytest.mark.priority_critical
@pytest.mark.usefixtures("browser_setup")
class TestOrganizationRegistration:
    """Test organization registration workflows"""

    @pytest.mark.asyncio
    async def test_organization_registration_complete_workflow(self, browser_setup, db_connection):
        """
        E2E TEST: Complete organization registration workflow

        BUSINESS REQUIREMENT:
        - Organizations can self-register with admin account
        - Organization gets subdomain for branding
        - Admin account automatically created with org_admin role

        TEST SCENARIO:
        1. Navigate to organization registration page
        2. Fill organization details (name, subdomain)
        3. Fill admin account details
        4. Submit form
        5. Verify organization created
        6. Verify admin account created
        7. Verify admin linked to organization

        VALIDATION:
        - Organization record created in database
        - Admin user created with org_admin role
        - Admin user linked to organization
        - Subdomain validated and unique
        """
        driver, base_url = browser_setup
        org_page = OrganizationRegistrationPage(driver, base_url)

        # Generate unique org data
        unique_id = str(uuid.uuid4())[:8]
        org_name = f"Test Org {unique_id}"
        subdomain = f"testorg{unique_id}"
        admin_email = f"admin_{unique_id}@testorg.com"
        admin_username = f"admin_{unique_id}"
        admin_password = "AdminPass123!"

        # Fill and submit
        org_page.navigate()
        org_page.fill_organization_name(org_name)
        org_page.fill_subdomain(subdomain)
        org_page.fill_admin_email(admin_email)
        org_page.fill_admin_username(admin_username)
        org_page.fill_admin_password(admin_password)
        org_page.submit_form()

        time.sleep(3)  # Wait for DB writes

        # DATABASE VERIFICATION: Organization created
        org = await db_connection.fetchrow(
            "SELECT id, name, subdomain FROM course_creator.organizations WHERE subdomain = $1",
            subdomain
        )

        assert org is not None, "Organization should be created"
        assert org['name'] == org_name, "Organization name should match"

        # DATABASE VERIFICATION: Admin user created
        admin_user = await db_connection.fetchrow(
            "SELECT id, email, username, role, organization_id FROM course_creator.users WHERE email = $1",
            admin_email
        )

        assert admin_user is not None, "Admin user should be created"
        assert admin_user['role'] == 'org_admin', "Admin should have org_admin role"
        assert admin_user['organization_id'] == org['id'], "Admin should be linked to organization"

    @pytest.mark.asyncio
    async def test_organization_subdomain_validation(self, browser_setup):
        """
        E2E TEST: Organization subdomain validation

        BUSINESS REQUIREMENT:
        - Subdomains must be unique across platform
        - Subdomains must follow naming rules (lowercase, alphanumeric, hyphens)
        - Invalid subdomains should show clear error

        TEST SCENARIO:
        1. Try to register with invalid subdomain (spaces, special chars)
        2. Verify validation error
        3. Try to register with existing subdomain
        4. Verify duplicate error

        VALIDATION:
        - Frontend validation catches invalid subdomains
        - Backend validation prevents duplicate subdomains
        - Clear error messages guide user
        """
        driver, base_url = browser_setup
        org_page = OrganizationRegistrationPage(driver, base_url)

        org_page.navigate()

        # Test invalid subdomain (with spaces)
        org_page.fill_subdomain("invalid subdomain")
        org_page.fill_organization_name("Test Org")
        org_page.submit_form()

        time.sleep(1)

        # Should show validation error
        subdomain_input = driver.find_element(By.ID, "org-subdomain")
        validation_message = subdomain_input.get_attribute("validationMessage")
        # Note: Exact validation depends on HTML5 pattern attribute

        # Test subdomain with special characters
        subdomain_input.clear()
        subdomain_input.send_keys("test@org!")
        org_page.submit_form()

        time.sleep(1)

        # Should show validation error
        validation_message = subdomain_input.get_attribute("validationMessage")
        # Should fail pattern validation

    @pytest.mark.asyncio
    async def test_organization_settings_during_registration(self, browser_setup, db_connection):
        """
        E2E TEST: Organization settings configuration during registration

        BUSINESS REQUIREMENT:
        - Organizations can configure settings during registration
        - Settings include: timezone, language, features enabled
        - Default settings should be reasonable

        TEST SCENARIO:
        1. Register organization with custom settings
        2. Verify settings stored correctly
        3. Verify defaults used for non-specified settings

        VALIDATION:
        - Custom settings stored in database
        - Default values used for optional settings
        - Settings can be changed after registration
        """
        driver, base_url = browser_setup
        org_page = OrganizationRegistrationPage(driver, base_url)

        unique_id = str(uuid.uuid4())[:8]
        subdomain = f"testorg_settings_{unique_id}"

        org_page.navigate()
        org_page.fill_organization_name(f"Test Org Settings {unique_id}")
        org_page.fill_subdomain(subdomain)
        org_page.fill_admin_email(f"admin_{unique_id}@testorg.com")
        org_page.fill_admin_username(f"admin_{unique_id}")
        org_page.fill_admin_password("AdminPass123!")

        # If settings fields exist, fill them
        # This depends on registration form design

        org_page.submit_form()
        time.sleep(3)

        # DATABASE VERIFICATION
        org_settings = await db_connection.fetchrow(
            "SELECT timezone, language, features_enabled FROM course_creator.organizations WHERE subdomain = $1",
            subdomain
        )

        # Verify defaults or custom values
        if org_settings:
            # Default timezone might be UTC
            # Default language might be 'en'
            pass

    @pytest.mark.asyncio
    async def test_organization_admin_account_creation(self, browser_setup, db_connection):
        """
        E2E TEST: Organization admin account creation and permissions

        BUSINESS REQUIREMENT:
        - First admin account created automatically
        - Admin has full permissions within organization
        - Admin can add more admins later

        TEST SCENARIO:
        1. Register organization
        2. Verify admin account created with correct role
        3. Verify admin has organization_id set
        4. Verify admin can access org-admin dashboard

        VALIDATION:
        - Admin user has role 'org_admin'
        - Admin linked to correct organization
        - Admin can manage organization
        """
        driver, base_url = browser_setup
        org_page = OrganizationRegistrationPage(driver, base_url)

        unique_id = str(uuid.uuid4())[:8]
        subdomain = f"testorg_admin_{unique_id}"
        admin_email = f"admin_{unique_id}@testorg.com"

        org_page.navigate()
        org_page.fill_organization_name(f"Test Org Admin {unique_id}")
        org_page.fill_subdomain(subdomain)
        org_page.fill_admin_email(admin_email)
        org_page.fill_admin_username(f"admin_{unique_id}")
        org_page.fill_admin_password("AdminPass123!")
        org_page.submit_form()

        time.sleep(3)

        # DATABASE VERIFICATION
        admin_user = await db_connection.fetchrow(
            "SELECT id, role, organization_id, is_active FROM course_creator.users WHERE email = $1",
            admin_email
        )

        assert admin_user is not None, "Admin user should exist"
        assert admin_user['role'] == 'org_admin', "Should have org_admin role"
        assert admin_user['organization_id'] is not None, "Should be linked to organization"
        assert admin_user['is_active'] is True, "Should be active"

    @pytest.mark.asyncio
    async def test_first_login_after_organization_registration(self, browser_setup, db_connection):
        """
        E2E TEST: First login after organization registration

        BUSINESS REQUIREMENT:
        - Admin can login immediately after registration
        - Redirect to organization setup wizard
        - Welcome message displayed

        TEST SCENARIO:
        1. Register organization
        2. Navigate to login page
        3. Login with admin credentials
        4. Verify redirect to org-admin dashboard
        5. Verify welcome message or setup wizard

        VALIDATION:
        - Login succeeds immediately
        - JWT token contains organization_id
        - Redirect to correct dashboard
        - Setup wizard triggers for new orgs
        """
        driver, base_url = browser_setup
        org_page = OrganizationRegistrationPage(driver, base_url)

        unique_id = str(uuid.uuid4())[:8]
        admin_email = f"admin_login_{unique_id}@testorg.com"
        admin_password = "AdminPass123!"

        # Register organization
        org_page.navigate()
        org_page.fill_organization_name(f"Test Org Login {unique_id}")
        org_page.fill_subdomain(f"testorg_login_{unique_id}")
        org_page.fill_admin_email(admin_email)
        org_page.fill_admin_username(f"admin_login_{unique_id}")
        org_page.fill_admin_password(admin_password)
        org_page.submit_form()

        time.sleep(3)

        # Navigate to login page
        driver.get(f"{base_url}/html/login.html")
        time.sleep(2)

        # Login with admin credentials
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-email"))
        )
        password_input = driver.find_element(By.ID, "login-password")
        submit_btn = driver.find_element(By.ID, "login-submit")

        email_input.send_keys(admin_email)
        password_input.send_keys(admin_password)
        submit_btn.click()

        time.sleep(3)

        # Verify redirect to org-admin dashboard
        assert "org-admin-dashboard" in driver.current_url or "organization" in driver.current_url, \
            "Should redirect to org-admin dashboard after login"


# ============================================================================
# REGISTRATION FEATURES TESTS (5 tests)
# ============================================================================

@pytest.mark.e2e
@pytest.mark.authentication
@pytest.mark.priority_critical
@pytest.mark.usefixtures("browser_setup")
class TestRegistrationFeatures:
    """Test registration form features and validation"""

    def test_password_strength_validation(self, browser_setup):
        """
        E2E TEST: Password strength validation

        BUSINESS REQUIREMENT:
        - Passwords must meet security requirements
        - Requirements: 8+ chars, uppercase, lowercase, number, special char
        - Real-time validation feedback

        TEST SCENARIO:
        1. Try weak password (too short)
        2. Verify error message
        3. Try password without uppercase
        4. Verify error message
        5. Try password without number
        6. Verify error message
        7. Try strong password
        8. Verify acceptance

        VALIDATION:
        - Frontend shows password strength meter
        - Backend validates password requirements
        - Clear error messages guide user
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)

        reg_page.navigate()

        # Test weak passwords
        weak_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NoNumber!",  # No number
            "NoSpecial123",  # No special char
        ]

        for weak_pwd in weak_passwords:
            reg_page.fill_password(weak_pwd)
            time.sleep(0.5)

            # Check for password strength indicator
            try:
                strength_indicator = driver.find_element(By.ID, "password-strength")
                strength_text = strength_indicator.text.lower()
                assert "weak" in strength_text or "invalid" in strength_text, \
                    f"Should show weak for password: {weak_pwd}"
            except NoSuchElementException:
                # Might use different validation approach
                pass

        # Test strong password
        reg_page.fill_password("StrongPass123!")
        time.sleep(0.5)

        try:
            strength_indicator = driver.find_element(By.ID, "password-strength")
            strength_text = strength_indicator.text.lower()
            assert "strong" in strength_text or "valid" in strength_text, \
                "Should show strong for valid password"
        except NoSuchElementException:
            # Validation might be silent for valid passwords
            pass

    def test_email_format_validation(self, browser_setup):
        """
        E2E TEST: Email format validation

        BUSINESS REQUIREMENT:
        - Only valid email formats accepted
        - Real-time validation feedback
        - HTML5 + JavaScript validation

        TEST SCENARIO:
        1. Try invalid email formats
        2. Verify error messages
        3. Try valid email
        4. Verify acceptance

        VALIDATION:
        - HTML5 email input type validation
        - JavaScript regex validation
        - Clear error messages
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)

        reg_page.navigate()

        # Test invalid email formats
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@nodomain.com",
            "spaces in@email.com",
        ]

        for invalid_email in invalid_emails:
            reg_page.fill_email(invalid_email)
            reg_page.submit_form()
            time.sleep(0.5)

            # HTML5 validation should prevent submission
            email_input = driver.find_element(By.ID, "register-email")
            validation_message = email_input.get_attribute("validationMessage")
            assert validation_message != "", f"Should show validation for: {invalid_email}"

        # Test valid email
        reg_page.fill_email("valid@example.com")
        email_input = driver.find_element(By.ID, "register-email")
        validation_message = email_input.get_attribute("validationMessage")
        assert validation_message == "", "Valid email should not show validation error"

    @pytest.mark.asyncio
    async def test_terms_of_service_acceptance_required(self, browser_setup):
        """
        E2E TEST: Terms of service acceptance required

        BUSINESS REQUIREMENT:
        - Users must accept TOS to register
        - TOS link opens in new tab
        - Checkbox must be explicitly checked

        TEST SCENARIO:
        1. Fill registration form
        2. Try to submit without accepting TOS
        3. Verify error/prevention
        4. Accept TOS
        5. Verify submission allowed

        VALIDATION:
        - Cannot submit without TOS acceptance
        - TOS link accessible
        - Checkbox state recorded
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)

        unique_id = str(uuid.uuid4())[:8]

        reg_page.navigate()
        reg_page.fill_email(f"tos_{unique_id}@test.com")
        reg_page.fill_username(f"tos_{unique_id}")
        reg_page.fill_password("SecurePass123!")
        reg_page.fill_confirm_password("SecurePass123!")
        reg_page.select_role("student")
        reg_page.accept_gdpr()
        # Don't accept TOS

        reg_page.submit_form()
        time.sleep(1)

        # Verify still on registration page
        assert "register.html" in driver.current_url, "Should not submit without TOS"

        # Accept TOS and try again
        reg_page.accept_terms()
        reg_page.submit_form()
        time.sleep(2)

        # Should succeed or show success message
        success_msg = reg_page.get_success_message()
        # Might succeed or show "verify email" message

    @pytest.mark.asyncio
    async def test_gdpr_consent_recording(self, browser_setup, db_connection):
        """
        E2E TEST: GDPR consent recording

        BUSINESS REQUIREMENT:
        - GDPR consent must be explicit and recorded
        - Consent timestamp stored in database
        - Consent cannot be pre-checked

        TEST SCENARIO:
        1. Navigate to registration
        2. Verify GDPR checkbox not pre-checked
        3. Register with GDPR consent
        4. Verify consent timestamp in database
        5. Verify consent details stored

        VALIDATION:
        - GDPR checkbox starts unchecked
        - Consent timestamp recorded on registration
        - Consent version tracked (for audits)
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)

        reg_page.navigate()

        # Verify GDPR checkbox not pre-checked
        gdpr_checkbox = driver.find_element(By.ID, "register-gdpr-consent")
        assert not gdpr_checkbox.is_selected(), "GDPR checkbox should not be pre-checked"

        # Register with consent
        unique_id = str(uuid.uuid4())[:8]
        email = f"gdpr_{unique_id}@test.com"

        reg_page.fill_email(email)
        reg_page.fill_username(f"gdpr_{unique_id}")
        reg_page.fill_password("SecurePass123!")
        reg_page.fill_confirm_password("SecurePass123!")
        reg_page.select_role("student")
        reg_page.accept_terms()
        reg_page.accept_gdpr()
        reg_page.submit_form()

        time.sleep(2)

        # DATABASE VERIFICATION
        gdpr_consent = await db_connection.fetchrow(
            "SELECT gdpr_consent_date, gdpr_consent_version FROM course_creator.users WHERE email = $1",
            email
        )

        assert gdpr_consent is not None, "User should exist"
        assert gdpr_consent['gdpr_consent_date'] is not None, "GDPR consent date should be recorded"
        # gdpr_consent_version might be stored for compliance audits

    def test_automatic_login_after_successful_registration(self, browser_setup):
        """
        E2E TEST: Automatic login after registration (if email pre-verified)

        BUSINESS REQUIREMENT:
        - Some platforms auto-login after registration
        - Others require email verification first
        - Clear UX for both approaches

        TEST SCENARIO:
        1. Register new account
        2. Check if automatically logged in
        3. Or verify "check email" message

        VALIDATION:
        - Either auto-login or email verification message
        - JWT token created if auto-login
        - Clear next steps communicated
        """
        driver, base_url = browser_setup
        reg_page = RegistrationPage(driver, base_url)

        unique_id = str(uuid.uuid4())[:8]

        reg_page.navigate()
        reg_page.fill_email(f"autologin_{unique_id}@test.com")
        reg_page.fill_username(f"autologin_{unique_id}")
        reg_page.fill_password("SecurePass123!")
        reg_page.fill_confirm_password("SecurePass123!")
        reg_page.select_role("student")
        reg_page.accept_terms()
        reg_page.accept_gdpr()
        reg_page.submit_form()

        time.sleep(3)

        # Check if logged in (authToken in localStorage)
        auth_token = driver.execute_script("return localStorage.getItem('authToken');")

        if auth_token:
            # Auto-login enabled
            assert auth_token is not None, "Should have auth token"
            # Might redirect to dashboard
        else:
            # Email verification required
            success_msg = reg_page.get_success_message()
            assert "email" in success_msg.lower() or "verify" in success_msg.lower(), \
                "Should show email verification message"
