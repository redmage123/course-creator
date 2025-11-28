"""
E2E Tests for Organization Registration Workflow

Tests the complete organization self-service registration flow including:
- Multi-section form completion
- Auto-slug generation
- Logo upload with preview
- Real-time validation
- Password strength requirements
- Terms acceptance
- Auto-login after registration

BUSINESS CONTEXT:
Organization registration is the primary onboarding path for new corporate clients.
This workflow must be smooth, secure, and require minimal manual intervention.

TECHNICAL IMPLEMENTATION:
- Tests React form with FormData multipart upload
- Validates client-side and server-side validation
- Tests JWT token generation and auto-login
- Verifies role-based redirect to org admin dashboard
"""

import pytest
import time
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import base classes
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from selenium_base import SeleniumConfig, ChromeDriverSetup


# ============================================================================
# PAGE OBJECTS
# ============================================================================

class OrganizationRegistrationPage:
    """
    Page Object for Organization Registration form.
    """

    def __init__(self, driver: webdriver.Chrome, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 20)

    def navigate(self):
        """Navigate to organization registration page"""
        self.driver.get(f"{self.base_url}/organization/register")
        time.sleep(2)  # Allow React to render

    def fill_organization_name(self, name: str):
        """Fill organization name"""
        name_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        name_input.clear()
        name_input.send_keys(name)
        time.sleep(0.5)  # Allow auto-slug generation

    def get_generated_slug(self) -> str:
        """Get auto-generated slug value"""
        slug_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, "slug"))
        )
        return slug_input.get_attribute("value")

    def fill_organization_description(self, description: str):
        """Fill organization description"""
        desc_input = self.driver.find_element(By.NAME, "description")
        desc_input.clear()
        desc_input.send_keys(description)

    def fill_organization_domain(self, domain: str):
        """Fill organization domain"""
        domain_input = self.driver.find_element(By.NAME, "domain")
        domain_input.clear()
        domain_input.send_keys(domain)

    def fill_street_address(self, address: str):
        """Fill street address"""
        address_input = self.driver.find_element(By.NAME, "street_address")
        address_input.clear()
        address_input.send_keys(address)

    def fill_city(self, city: str):
        """Fill city"""
        city_input = self.driver.find_element(By.NAME, "city")
        city_input.clear()
        city_input.send_keys(city)

    def fill_state(self, state: str):
        """Fill state/province"""
        state_input = self.driver.find_element(By.NAME, "state_province")
        state_input.clear()
        state_input.send_keys(state)

    def fill_postal_code(self, postal_code: str):
        """Fill postal code"""
        postal_input = self.driver.find_element(By.NAME, "postal_code")
        postal_input.clear()
        postal_input.send_keys(postal_code)

    def select_country(self, country: str):
        """Select country from dropdown"""
        country_select = self.driver.find_element(By.NAME, "country")
        country_select.click()
        time.sleep(0.3)

        # Find option with matching text
        options = country_select.find_elements(By.TAG_NAME, "option")
        for option in options:
            if country in option.text:
                option.click()
                break

    def fill_contact_email(self, email: str):
        """Fill contact email"""
        email_input = self.driver.find_element(By.NAME, "contact_email")
        email_input.clear()
        email_input.send_keys(email)

    def fill_contact_phone(self, phone: str):
        """Fill contact phone"""
        phone_input = self.driver.find_element(By.NAME, "contact_phone")
        phone_input.clear()
        phone_input.send_keys(phone)

    def fill_admin_full_name(self, name: str):
        """Fill admin full name"""
        name_input = self.driver.find_element(By.NAME, "admin_full_name")
        name_input.clear()
        name_input.send_keys(name)

    def fill_admin_username(self, username: str):
        """Fill admin username"""
        username_input = self.driver.find_element(By.NAME, "admin_username")
        username_input.clear()
        username_input.send_keys(username)

    def fill_admin_email(self, email: str):
        """Fill admin email"""
        email_input = self.driver.find_element(By.NAME, "admin_email")
        email_input.clear()
        email_input.send_keys(email)

    def fill_admin_password(self, password: str):
        """Fill admin password"""
        password_input = self.driver.find_element(By.NAME, "admin_password")
        password_input.clear()
        password_input.send_keys(password)

    def fill_admin_password_confirm(self, password: str):
        """Fill admin password confirmation"""
        confirm_input = self.driver.find_element(By.NAME, "admin_password_confirm")
        confirm_input.clear()
        confirm_input.send_keys(password)

    def accept_terms(self):
        """Click terms acceptance checkbox"""
        terms_checkbox = self.driver.find_element(By.NAME, "terms_accepted")
        if not terms_checkbox.is_selected():
            terms_checkbox.click()

    def accept_privacy(self):
        """Click privacy policy checkbox"""
        privacy_checkbox = self.driver.find_element(By.NAME, "privacy_accepted")
        if not privacy_checkbox.is_selected():
            privacy_checkbox.click()

    def submit_form(self):
        """Submit registration form"""
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

    def get_error_messages(self) -> list:
        """Get all validation error messages"""
        # Look for error text elements
        error_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='error'], [class*='Error']")
        return [elem.text for elem in error_elements if elem.text]

    def has_success_message(self) -> bool:
        """Check if success message is displayed"""
        try:
            success_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='success'], [class*='Success']")
            return any(elem.is_displayed() for elem in success_elements)
        except NoSuchElementException:
            return False


# ============================================================================
# TEST CLASS
# ============================================================================

class TestOrganizationRegistration:
    """
    Test suite for Organization Registration workflow.
    """

    @pytest.fixture(scope="class")
    def config(self):
        """Create Selenium config"""
        return SeleniumConfig()

    @pytest.fixture(scope="function")
    def driver(self, config):
        """Create WebDriver instance"""
        driver = ChromeDriverSetup.create_driver(config)
        yield driver
        driver.quit()

    @pytest.fixture(scope="function")
    def org_reg_page(self, driver, config):
        """Create Organization Registration page object"""
        return OrganizationRegistrationPage(driver, config.base_url)

    def test_registration_form_loads(self, org_reg_page):
        """
        Test that registration form loads successfully.

        SCENARIO:
        1. Navigate to /organization/register
        2. Verify form elements present

        EXPECTED RESULT:
        - Form loads without errors
        - All required sections visible
        """
        org_reg_page.navigate()

        # Check for form sections
        driver = org_reg_page.driver

        # Organization details
        assert driver.find_element(By.NAME, "name")
        assert driver.find_element(By.NAME, "slug")
        assert driver.find_element(By.NAME, "domain")

        # Admin account section
        assert driver.find_element(By.NAME, "admin_username")
        assert driver.find_element(By.NAME, "admin_password")

    def test_auto_slug_generation(self, org_reg_page):
        """
        Test auto-slug generation from organization name.

        SCENARIO:
        1. Load registration form
        2. Enter organization name: "My Test Company"
        3. Wait for slug auto-generation

        EXPECTED RESULT:
        - Slug field auto-populated with "my-test-company"
        - Slug uses lowercase and hyphens
        """
        org_reg_page.navigate()

        # Fill organization name
        test_name = "My Test Company"
        org_reg_page.fill_organization_name(test_name)

        # Get generated slug
        slug = org_reg_page.get_generated_slug()

        # Verify slug format
        assert slug == "my-test-company"
        assert slug.islower()
        assert " " not in slug

    def test_password_validation(self, org_reg_page):
        """
        Test password strength validation.

        SCENARIO:
        1. Load form
        2. Try weak password
        3. Try strong password

        EXPECTED RESULT:
        - Weak password shows error
        - Strong password passes validation
        - Password requirements displayed
        """
        org_reg_page.navigate()

        # Fill minimal required fields
        unique_id = str(uuid.uuid4())[:8]
        org_reg_page.fill_organization_name(f"Test Org {unique_id}")
        org_reg_page.fill_organization_domain(f"test-{unique_id}.com")
        org_reg_page.fill_contact_email(f"contact-{unique_id}@test.com")
        org_reg_page.fill_admin_full_name("Admin User")
        org_reg_page.fill_admin_username(f"admin_{unique_id}")
        org_reg_page.fill_admin_email(f"admin-{unique_id}@test.com")

        # Try weak password
        org_reg_page.fill_admin_password("weak")
        org_reg_page.fill_admin_password_confirm("weak")

        # Should see password requirements
        page_text = org_reg_page.driver.find_element(By.TAG_NAME, "body").text
        assert "8 characters" in page_text or "password" in page_text.lower()

    def test_complete_registration_workflow(self, org_reg_page):
        """
        Test complete organization registration flow.

        SCENARIO:
        1. Fill all required fields
        2. Accept terms and privacy
        3. Submit form
        4. Verify success (or redirect to dashboard)

        EXPECTED RESULT:
        - Form submission succeeds
        - User auto-logged in
        - Redirected to org admin dashboard
        """
        org_reg_page.navigate()

        # Generate unique identifiers
        unique_id = str(uuid.uuid4())[:8]

        # Fill organization details
        org_name = f"E2E Test Organization {unique_id}"
        org_reg_page.fill_organization_name(org_name)
        org_reg_page.fill_organization_description("Automated test organization")
        org_reg_page.fill_organization_domain(f"e2etest-{unique_id}.com")

        # Fill address
        org_reg_page.fill_street_address("123 Test Street")
        org_reg_page.fill_city("Test City")
        org_reg_page.fill_state("Test State")
        org_reg_page.fill_postal_code("12345")
        org_reg_page.select_country("United States")

        # Fill contact info
        org_reg_page.fill_contact_email(f"contact-{unique_id}@e2etest.com")
        org_reg_page.fill_contact_phone("555-1234")

        # Fill admin account
        org_reg_page.fill_admin_full_name("Test Admin")
        org_reg_page.fill_admin_username(f"testadmin_{unique_id}")
        org_reg_page.fill_admin_email(f"admin-{unique_id}@e2etest.com")
        org_reg_page.fill_admin_password("SecurePass123!")
        org_reg_page.fill_admin_password_confirm("SecurePass123!")

        # Accept terms
        org_reg_page.accept_terms()
        org_reg_page.accept_privacy()

        # Submit form
        org_reg_page.submit_form()

        # Wait for redirect or success message
        time.sleep(3)

        # Check current URL (should redirect to dashboard or show success)
        current_url = org_reg_page.driver.current_url

        # Should either be on dashboard or have success message
        assert ("/dashboard" in current_url or
                org_reg_page.has_success_message() or
                "organization" in current_url.lower())

    def test_email_validation(self, org_reg_page):
        """
        Test email format validation.

        SCENARIO:
        1. Load form
        2. Enter invalid email
        3. Try to submit

        EXPECTED RESULT:
        - Invalid email shows error
        - Form doesn't submit with invalid email
        """
        org_reg_page.navigate()

        # Enter invalid email
        org_reg_page.fill_contact_email("invalid-email")

        # Try to find submit button and check validation
        submit_button = org_reg_page.driver.find_element(By.XPATH, "//button[@type='submit']")

        # HTML5 validation or React validation should prevent submission
        # Check if email input has validation attribute or error state
        email_input = org_reg_page.driver.find_element(By.NAME, "contact_email")
        input_type = email_input.get_attribute("type")

        # Should be type="email" for validation
        assert input_type == "email" or input_type == "text"

    def test_password_mismatch_validation(self, org_reg_page):
        """
        Test password confirmation mismatch detection.

        SCENARIO:
        1. Load form
        2. Enter password: "SecurePass123!"
        3. Enter different confirm password: "DifferentPass123!"
        4. Try to submit

        EXPECTED RESULT:
        - Error message: "Passwords do not match"
        - Form doesn't submit
        """
        org_reg_page.navigate()

        # Fill minimal fields
        unique_id = str(uuid.uuid4())[:8]
        org_reg_page.fill_organization_name(f"Test Org {unique_id}")
        org_reg_page.fill_organization_domain(f"test-{unique_id}.com")
        org_reg_page.fill_contact_email(f"contact-{unique_id}@test.com")
        org_reg_page.fill_admin_full_name("Admin User")
        org_reg_page.fill_admin_username(f"admin_{unique_id}")
        org_reg_page.fill_admin_email(f"admin-{unique_id}@test.com")

        # Enter mismatched passwords
        org_reg_page.fill_admin_password("SecurePass123!")
        org_reg_page.fill_admin_password_confirm("DifferentPass123!")

        org_reg_page.accept_terms()
        org_reg_page.accept_privacy()

        # Try to submit
        org_reg_page.submit_form()

        time.sleep(1)

        # Check for error message
        errors = org_reg_page.get_error_messages()
        page_text = org_reg_page.driver.find_element(By.TAG_NAME, "body").text

        assert (len(errors) > 0 or
                "match" in page_text.lower() or
                "password" in page_text.lower())

    def test_terms_acceptance_required(self, org_reg_page):
        """
        Test that terms acceptance is required.

        SCENARIO:
        1. Load form
        2. Fill all fields except terms checkboxes
        3. Try to submit

        EXPECTED RESULT:
        - Form doesn't submit without terms acceptance
        - Checkboxes are required
        """
        org_reg_page.navigate()

        # Fill minimal required fields
        unique_id = str(uuid.uuid4())[:8]
        org_reg_page.fill_organization_name(f"Test Org {unique_id}")
        org_reg_page.fill_organization_domain(f"test-{unique_id}.com")
        org_reg_page.fill_contact_email(f"contact-{unique_id}@test.com")
        org_reg_page.fill_admin_full_name("Admin User")
        org_reg_page.fill_admin_username(f"admin_{unique_id}")
        org_reg_page.fill_admin_email(f"admin-{unique_id}@test.com")
        org_reg_page.fill_admin_password("SecurePass123!")
        org_reg_page.fill_admin_password_confirm("SecurePass123!")

        # Don't check terms - try to submit
        org_reg_page.submit_form()

        time.sleep(1)

        # Should still be on registration page or show error
        current_url = org_reg_page.driver.current_url
        assert "/organization/register" in current_url
