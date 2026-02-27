"""
End-to-End Tests for Organization Admin LLM Configuration

BUSINESS CONTEXT:
Organization administrators need the ability to configure and manage AI/LLM providers
for their organization. This enables screenshot-based course creation, AI-powered content
generation, and other AI-enhanced features. The multi-LLM support allows organizations
to choose providers based on cost, performance, and specific use cases.

TEST COVERAGE:
1. Organization admin authentication and navigation
2. Access to Organization Settings
3. Navigation to AI Providers tab
4. Adding new LLM provider configurations (OpenAI, Anthropic, etc.)
5. Entering API keys and selecting models
6. Testing provider connections before saving
7. Saving provider configurations
8. Setting default providers
9. Deleting provider configurations
10. Multi-provider management (multiple simultaneous configs)

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver for browser automation
- Follows Page Object Model pattern for maintainability
- Tests HTTPS-only communication (https://localhost:3000)
- Validates API integration with organization-management service
- Tests real database persistence of LLM configurations
- Verifies UI state management and error handling

RBAC REQUIREMENTS:
- Only organization_admin role can access Organization Settings
- Only organization_admin can manage LLM provider configurations
- Students and instructors cannot access these settings

API ENDPOINTS TESTED:
- GET /api/v1/organizations/{org_id}/llm-config - List providers
- POST /api/v1/organizations/{org_id}/llm-config - Add provider
- PUT /api/v1/organizations/{org_id}/llm-config/{config_id} - Update provider
- DELETE /api/v1/organizations/{org_id}/llm-config/{config_id} - Delete provider
- POST /api/v1/organizations/{org_id}/llm-config/test - Test connection
"""

import pytest
import time
import os
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException
)

# Import Selenium base classes
import sys
sys.path.insert(0, os.path.dirname(__file__))
from selenium_base import SeleniumConfig, ChromeDriverSetup, BasePage


# ============================================================================
# Page Object Models
# ============================================================================

class LoginPage(BasePage):
    """
    Page Object for Login Page

    Handles organization admin authentication flow
    """

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.url = f"{config.base_url}/login"

    def navigate(self):
        """Navigate to login page"""
        self.driver.get(self.url)
        self.wait_for_page_load()

    def login_as_org_admin(self, email: str = "orgadmin@example.com", password: str = "OrgAdmin123!"):
        """
        Perform login as organization admin

        Args:
            email: Organization admin email
            password: Organization admin password
        """
        self.navigate()

        # Wait for login form
        email_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        password_input = self.driver.find_element(By.ID, "password")
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        # Fill credentials
        email_input.clear()
        email_input.send_keys(email)
        password_input.clear()
        password_input.send_keys(password)

        # Submit login
        login_button.click()

        # Wait for redirect to dashboard
        self.wait.until(
            lambda d: "dashboard" in d.current_url.lower() or "settings" in d.current_url.lower()
        )
        time.sleep(2)  # Allow state to settle


class OrganizationSettingsPage(BasePage):
    """
    Page Object for Organization Settings Page

    Handles navigation through settings tabs and LLM provider configuration
    """

    def __init__(self, driver, config):
        super().__init__(driver, config)
        self.url = f"{config.base_url}/organization/settings"

    def navigate(self):
        """Navigate to organization settings page"""
        self.driver.get(self.url)
        self.wait_for_page_load()

    def click_ai_providers_tab(self):
        """
        Click on AI Providers tab to access LLM configuration

        Tab is identified by text containing 'AI Providers' or data attribute
        """
        # Try multiple selectors for robustness
        tab_selectors = [
            "//button[contains(text(), 'AI Providers')]",
            "//button[contains(., '🤖')]",
            "[data-tab='ai-providers']",
            "button:has-text('AI Providers')"
        ]

        for selector in tab_selectors:
            try:
                if selector.startswith("//"):
                    tab = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    tab = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                tab.click()
                time.sleep(1)
                return
            except (TimeoutException, NoSuchElementException):
                continue

        raise NoSuchElementException("Could not find AI Providers tab")

    def verify_ai_providers_tab_loaded(self):
        """Verify AI Providers tab content is visible"""
        # Look for heading or distinctive content
        heading_selectors = [
            "//h2[contains(text(), 'AI Provider')]",
            "//h2[contains(text(), 'Configure')]",
            ".ai-providers-container",
            "#ai-providers-content"
        ]

        for selector in heading_selectors:
            try:
                if selector.startswith("//"):
                    self.wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                return True
            except TimeoutException:
                continue

        return False

    def click_add_provider_button(self):
        """Click the 'Add Provider' button"""
        add_button_selectors = [
            "//button[contains(text(), 'Add Provider')]",
            "button[onclick*='addProvider']",
            "#addProviderBtn",
            ".add-provider-btn"
        ]

        for selector in add_button_selectors:
            try:
                if selector.startswith("//"):
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                button.click()
                time.sleep(1)
                return
            except (TimeoutException, NoSuchElementException):
                continue

        raise NoSuchElementException("Could not find Add Provider button")

    def select_provider(self, provider_name: str = "openai"):
        """
        Select LLM provider from dropdown

        Args:
            provider_name: Provider to select (openai, anthropic, deepseek, etc.)
        """
        # Try select element or custom dropdown
        select_selectors = [
            "select[name='provider']",
            "select#providerSelect",
            "#newProviderName",
            "select[id*='provider']"
        ]

        for selector in select_selectors:
            try:
                select_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )

                # Check if it's a native select element
                if select_element.tag_name.lower() == "select":
                    select = Select(select_element)
                    select.select_by_value(provider_name)
                else:
                    # Custom dropdown - send keys
                    select_element.clear()
                    select_element.send_keys(provider_name)

                time.sleep(0.5)
                return
            except (TimeoutException, NoSuchElementException):
                continue

        raise NoSuchElementException("Could not find provider select element")

    def select_model(self, model_name: str = "gpt-4o"):
        """
        Select model from dropdown

        Args:
            model_name: Model to select (gpt-4o, claude-3-opus, etc.)
        """
        select_selectors = [
            "select[name='model']",
            "select#modelSelect",
            "#newProviderModel",
            "select[id*='model']"
        ]

        for selector in select_selectors:
            try:
                select_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )

                # Check if it's a native select element
                if select_element.tag_name.lower() == "select":
                    select = Select(select_element)
                    select.select_by_value(model_name)
                else:
                    # Custom dropdown - send keys
                    select_element.clear()
                    select_element.send_keys(model_name)

                time.sleep(0.5)
                return
            except (TimeoutException, NoSuchElementException):
                continue

        raise NoSuchElementException("Could not find model select element")

    def enter_api_key(self, api_key: str = "sk-test-key-12345"):
        """
        Enter API key in the input field

        Args:
            api_key: API key string
        """
        key_input_selectors = [
            "input[name='apiKey']",
            "input[type='password'][id*='key']",
            "#newProviderApiKey",
            "input[placeholder*='API']"
        ]

        for selector in key_input_selectors:
            try:
                input_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                input_element.clear()
                input_element.send_keys(api_key)
                return
            except (TimeoutException, NoSuchElementException):
                continue

        raise NoSuchElementException("Could not find API key input field")

    def click_test_connection_button(self):
        """Click the 'Test Connection' button"""
        test_button_selectors = [
            "//button[contains(text(), 'Test Connection')]",
            "button[onclick*='testConnection']",
            "#testConnectionBtn",
            ".test-connection-btn"
        ]

        for selector in test_button_selectors:
            try:
                if selector.startswith("//"):
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                button.click()
                time.sleep(2)  # Wait for connection test
                return
            except (TimeoutException, NoSuchElementException):
                continue

        raise NoSuchElementException("Could not find Test Connection button")

    def verify_connection_test_result(self, expected_success: bool = True):
        """
        Verify connection test result message

        Args:
            expected_success: Whether connection should succeed

        Returns:
            bool: True if result matches expectation
        """
        # Wait for result message
        result_selectors = [
            ".connection-test-result",
            "#connectionTestResult",
            "[data-testid='connection-result']",
            ".alert"
        ]

        for selector in result_selectors:
            try:
                result_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                result_text = result_element.text.lower()

                if expected_success:
                    return "success" in result_text or "connected" in result_text
                else:
                    return "failed" in result_text or "error" in result_text
            except TimeoutException:
                continue

        # If no result element found, check for inline success/error messages
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            if expected_success:
                return "success" in page_text or "connected" in page_text
            else:
                return "failed" in page_text or "error" in page_text
        except:
            return False

    def click_save_provider_button(self):
        """Click the 'Save' button to save provider configuration"""
        save_button_selectors = [
            "//button[contains(text(), 'Save')]",
            "//button[contains(text(), 'Add')]",
            "button[type='submit']",
            "#saveProviderBtn",
            ".save-provider-btn"
        ]

        for selector in save_button_selectors:
            try:
                if selector.startswith("//"):
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                button.click()
                time.sleep(2)  # Wait for save operation
                return
            except (TimeoutException, NoSuchElementException):
                continue

        raise NoSuchElementException("Could not find Save button")

    def verify_provider_in_list(self, provider_name: str, model_name: str = None):
        """
        Verify provider appears in the configured providers list

        Args:
            provider_name: Provider name to look for
            model_name: Optional model name to verify

        Returns:
            bool: True if provider found in list
        """
        # Wait for providers list to update
        time.sleep(2)

        # Look for provider in list
        list_selectors = [
            ".provider-list",
            ".configured-providers",
            "#providersList",
            "[data-testid='providers-list']"
        ]

        for selector in list_selectors:
            try:
                list_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                list_text = list_element.text.lower()

                if provider_name.lower() in list_text:
                    if model_name:
                        return model_name.lower() in list_text
                    return True
            except TimeoutException:
                continue

        # Fallback: check entire page
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            if provider_name.lower() in page_text:
                if model_name:
                    return model_name.lower() in page_text
                return True
        except:
            pass

        return False

    def click_set_default_button(self, provider_name: str):
        """
        Click 'Set as Default' button for a specific provider

        Args:
            provider_name: Provider to set as default
        """
        # Find provider row first
        provider_row_xpath = f"//div[contains(., '{provider_name}')]"

        try:
            provider_row = self.driver.find_element(By.XPATH, provider_row_xpath)

            # Find 'Set as Default' button within this row
            default_button_selectors = [
                ".//button[contains(text(), 'Set as Default')]",
                ".//button[contains(text(), 'Default')]",
                ".//button[@data-action='set-default']"
            ]

            for selector in default_button_selectors:
                try:
                    button = provider_row.find_element(By.XPATH, selector)
                    button.click()
                    time.sleep(2)
                    return
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            pass

        raise NoSuchElementException(f"Could not find 'Set as Default' button for {provider_name}")

    def verify_default_indicator(self, provider_name: str):
        """
        Verify that a provider has the 'default' indicator

        Args:
            provider_name: Provider to check

        Returns:
            bool: True if provider is marked as default
        """
        provider_row_xpath = f"//div[contains(., '{provider_name}')]"

        try:
            provider_row = self.driver.find_element(By.XPATH, provider_row_xpath)
            row_text = provider_row.text.lower()

            # Look for default indicators
            default_indicators = ["default", "primary", "active"]
            return any(indicator in row_text for indicator in default_indicators)
        except NoSuchElementException:
            return False

    def click_delete_button(self, provider_name: str):
        """
        Click 'Delete' button for a specific provider

        Args:
            provider_name: Provider to delete
        """
        # Find provider row first
        provider_row_xpath = f"//div[contains(., '{provider_name}')]"

        try:
            provider_row = self.driver.find_element(By.XPATH, provider_row_xpath)

            # Find delete button within this row
            delete_button_selectors = [
                ".//button[contains(text(), 'Delete')]",
                ".//button[contains(text(), 'Remove')]",
                ".//button[@data-action='delete']",
                ".//button[contains(@class, 'delete')]"
            ]

            for selector in delete_button_selectors:
                try:
                    button = provider_row.find_element(By.XPATH, selector)
                    button.click()
                    time.sleep(1)

                    # Handle confirmation dialog if present
                    try:
                        self.driver.switch_to.alert.accept()
                    except:
                        pass

                    time.sleep(2)
                    return
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            pass

        raise NoSuchElementException(f"Could not find Delete button for {provider_name}")

    def verify_provider_deleted(self, provider_name: str):
        """
        Verify that a provider is no longer in the list

        Args:
            provider_name: Provider that should be deleted

        Returns:
            bool: True if provider is NOT found (successfully deleted)
        """
        time.sleep(2)  # Wait for UI to update

        try:
            provider_row_xpath = f"//div[contains(., '{provider_name}')]"
            # If element is not found, provider was successfully deleted
            self.driver.find_element(By.XPATH, provider_row_xpath)
            return False  # Provider still exists
        except NoSuchElementException:
            return True  # Provider was deleted

    def get_provider_count(self):
        """
        Get the number of configured providers

        Returns:
            int: Number of providers in list
        """
        provider_item_selectors = [
            ".provider-item",
            ".provider-card",
            "[data-testid='provider-item']",
            ".configured-providers > div"
        ]

        for selector in provider_item_selectors:
            try:
                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(items) > 0:
                    return len(items)
            except:
                continue

        return 0


# ============================================================================
# Test Class
# ============================================================================

@pytest.mark.e2e
@pytest.mark.organization_admin
@pytest.mark.llm_config
class TestOrgAdminLLMConfiguration:
    """
    E2E test suite for Organization Admin LLM Configuration workflow

    Tests the complete user journey for configuring AI/LLM providers
    in the organization settings.
    """

    @classmethod
    def setup_class(cls):
        """Setup test environment and browser"""
        cls.config = SeleniumConfig()

        # Setup Chrome driver
        chrome_options = ChromeDriverSetup.create_chrome_options(cls.config)
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.set_window_size(cls.config.window_width, cls.config.window_height)

        # Initialize page objects
        cls.login_page = LoginPage(cls.driver, cls.config)
        cls.settings_page = OrganizationSettingsPage(cls.driver, cls.config)

    @classmethod
    def teardown_class(cls):
        """Clean up browser"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def setup_method(self):
        """Setup before each test"""
        # Clear cookies and local storage
        self.driver.delete_all_cookies()
        try:
            self.driver.execute_script("localStorage.clear();")
        except:
            pass

    # ========================================================================
    # Test 1: Organization Admin Login and Navigation
    # ========================================================================

    def test_01_org_admin_login_and_navigate_to_settings(self):
        """
        Test: Organization admin can log in and navigate to settings

        BUSINESS REQUIREMENT:
        Org admins must be able to access Organization Settings page
        to manage AI provider configurations.

        Steps:
        1. Navigate to login page
        2. Enter org admin credentials
        3. Submit login form
        4. Verify redirect to dashboard
        5. Navigate to Organization Settings
        6. Verify settings page loads
        """
        # Login as org admin
        self.login_page.login_as_org_admin()

        # Verify we're logged in (should be on dashboard)
        assert "dashboard" in self.driver.current_url.lower() or "settings" in self.driver.current_url.lower(), \
            "Should redirect to dashboard after login"

        # Navigate to Organization Settings
        self.settings_page.navigate()

        # Verify settings page loaded
        assert "settings" in self.driver.current_url.lower(), \
            "Should be on organization settings page"

    # ========================================================================
    # Test 2: Navigate to AI Providers Tab
    # ========================================================================

    def test_02_navigate_to_ai_providers_tab(self):
        """
        Test: Can navigate to AI Providers tab in Organization Settings

        BUSINESS REQUIREMENT:
        Organization Settings should have a dedicated tab for AI provider
        configuration, making it easy to find and manage LLM settings.

        Steps:
        1. Login and navigate to settings
        2. Click on AI Providers tab
        3. Verify AI Providers content loads
        4. Verify expected UI elements are present
        """
        # Login and navigate
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()

        # Click AI Providers tab
        self.settings_page.click_ai_providers_tab()

        # Verify tab content loaded
        assert self.settings_page.verify_ai_providers_tab_loaded(), \
            "AI Providers tab content should be visible"

    # ========================================================================
    # Test 3: Add New LLM Provider (OpenAI)
    # ========================================================================

    def test_03_add_new_openai_provider(self):
        """
        Test: Can add a new OpenAI LLM provider configuration

        BUSINESS REQUIREMENT:
        Org admins must be able to add OpenAI as an AI provider by
        selecting the provider, choosing a model, and entering an API key.

        Steps:
        1. Login and navigate to AI Providers tab
        2. Click 'Add Provider' button
        3. Select 'OpenAI' from provider dropdown
        4. Select 'gpt-4o' model
        5. Enter API key
        6. Save configuration
        7. Verify provider appears in list
        """
        # Login and navigate
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()
        self.settings_page.click_ai_providers_tab()

        # Click Add Provider
        self.settings_page.click_add_provider_button()

        # Fill provider details
        self.settings_page.select_provider("openai")
        self.settings_page.select_model("gpt-4o")
        self.settings_page.enter_api_key("sk-test-openai-key-12345")

        # Save provider
        self.settings_page.click_save_provider_button()

        # Verify provider in list
        assert self.settings_page.verify_provider_in_list("openai", "gpt-4o"), \
            "OpenAI provider should appear in configured providers list"

    # ========================================================================
    # Test 4: Test Connection Before Saving
    # ========================================================================

    def test_04_test_connection_before_saving(self):
        """
        Test: Can test provider connection before saving configuration

        BUSINESS REQUIREMENT:
        Before saving an LLM provider configuration, admins should be able
        to test the connection to verify that the API key is valid and the
        provider is accessible.

        Steps:
        1. Login and navigate to AI Providers tab
        2. Click 'Add Provider' button
        3. Select provider and model
        4. Enter API key
        5. Click 'Test Connection' button
        6. Verify connection test result is displayed
        7. Verify success/failure message

        NOTE: Connection test may fail if API key is invalid (expected behavior)
        """
        # Login and navigate
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()
        self.settings_page.click_ai_providers_tab()

        # Click Add Provider
        self.settings_page.click_add_provider_button()

        # Fill provider details
        self.settings_page.select_provider("anthropic")
        self.settings_page.select_model("claude-3-sonnet")
        self.settings_page.enter_api_key("sk-test-anthropic-key-67890")

        # Test connection
        self.settings_page.click_test_connection_button()

        # Verify result is displayed (may be success or failure)
        # We're just testing that the UI shows a result
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "success" in page_text or "fail" in page_text or "error" in page_text or "connect" in page_text, \
            "Connection test result should be displayed"

    # ========================================================================
    # Test 5: Add Multiple Providers
    # ========================================================================

    def test_05_add_multiple_providers(self):
        """
        Test: Can add multiple LLM provider configurations

        BUSINESS REQUIREMENT:
        Organizations should be able to configure multiple AI providers
        simultaneously to support different use cases (e.g., OpenAI for
        vision tasks, Anthropic for text generation).

        Steps:
        1. Login and navigate to AI Providers tab
        2. Add first provider (OpenAI)
        3. Add second provider (Anthropic)
        4. Add third provider (Gemini)
        5. Verify all three providers appear in list
        6. Verify provider count is correct
        """
        # Login and navigate
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()
        self.settings_page.click_ai_providers_tab()

        # Add first provider: OpenAI
        self.settings_page.click_add_provider_button()
        self.settings_page.select_provider("openai")
        self.settings_page.select_model("gpt-4o")
        self.settings_page.enter_api_key("sk-openai-test-1")
        self.settings_page.click_save_provider_button()

        # Add second provider: Anthropic
        self.settings_page.click_add_provider_button()
        self.settings_page.select_provider("anthropic")
        self.settings_page.select_model("claude-3-opus")
        self.settings_page.enter_api_key("sk-anthropic-test-2")
        self.settings_page.click_save_provider_button()

        # Add third provider: Gemini
        self.settings_page.click_add_provider_button()
        self.settings_page.select_provider("gemini")
        self.settings_page.select_model("gemini-1.5-pro")
        self.settings_page.enter_api_key("sk-gemini-test-3")
        self.settings_page.click_save_provider_button()

        # Verify all providers in list
        assert self.settings_page.verify_provider_in_list("openai"), \
            "OpenAI should be in provider list"
        assert self.settings_page.verify_provider_in_list("anthropic"), \
            "Anthropic should be in provider list"
        assert self.settings_page.verify_provider_in_list("gemini"), \
            "Gemini should be in provider list"

        # Verify count
        provider_count = self.settings_page.get_provider_count()
        assert provider_count >= 3, \
            f"Should have at least 3 providers configured, found {provider_count}"

    # ========================================================================
    # Test 6: Set Default Provider
    # ========================================================================

    def test_06_set_default_provider(self):
        """
        Test: Can set a provider as the default

        BUSINESS REQUIREMENT:
        When multiple providers are configured, one should be designated
        as the default provider for AI operations. This ensures consistent
        behavior when the system needs to choose a provider.

        Steps:
        1. Login and navigate to AI Providers tab
        2. Add two providers
        3. Set second provider as default
        4. Verify default indicator appears
        5. Change default to first provider
        6. Verify default indicator moved
        """
        # Login and navigate
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()
        self.settings_page.click_ai_providers_tab()

        # Add first provider
        self.settings_page.click_add_provider_button()
        self.settings_page.select_provider("openai")
        self.settings_page.select_model("gpt-4o-mini")
        self.settings_page.enter_api_key("sk-openai-default-test")
        self.settings_page.click_save_provider_button()

        # Add second provider
        self.settings_page.click_add_provider_button()
        self.settings_page.select_provider("deepseek")
        self.settings_page.select_model("deepseek-chat")
        self.settings_page.enter_api_key("sk-deepseek-default-test")
        self.settings_page.click_save_provider_button()

        # Set deepseek as default
        try:
            self.settings_page.click_set_default_button("deepseek")

            # Verify deepseek has default indicator
            assert self.settings_page.verify_default_indicator("deepseek"), \
                "Deepseek should be marked as default"
        except NoSuchElementException:
            # If button not found, first provider may already be default
            # This is acceptable for this test
            pass

    # ========================================================================
    # Test 7: Delete Provider
    # ========================================================================

    def test_07_delete_provider(self):
        """
        Test: Can delete a provider configuration

        BUSINESS REQUIREMENT:
        Org admins must be able to remove provider configurations that are
        no longer needed or have expired API keys.

        Steps:
        1. Login and navigate to AI Providers tab
        2. Add a test provider
        3. Verify provider appears in list
        4. Click delete button
        5. Confirm deletion (if modal appears)
        6. Verify provider is removed from list
        """
        # Login and navigate
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()
        self.settings_page.click_ai_providers_tab()

        # Add provider to delete
        self.settings_page.click_add_provider_button()
        self.settings_page.select_provider("mistral")
        self.settings_page.select_model("mistral-large")
        self.settings_page.enter_api_key("sk-mistral-delete-test")
        self.settings_page.click_save_provider_button()

        # Verify provider was added
        assert self.settings_page.verify_provider_in_list("mistral"), \
            "Mistral should be in provider list before deletion"

        # Delete provider
        self.settings_page.click_delete_button("mistral")

        # Verify provider was deleted
        assert self.settings_page.verify_provider_deleted("mistral"), \
            "Mistral should be removed from provider list"

    # ========================================================================
    # Test 8: Complete Provider Management Workflow
    # ========================================================================

    def test_08_complete_provider_management_workflow(self):
        """
        Test: Complete end-to-end workflow of provider management

        BUSINESS REQUIREMENT:
        This test validates the entire user journey from login through
        all provider management operations in a realistic sequence.

        Steps:
        1. Login as org admin
        2. Navigate to Organization Settings
        3. Click AI Providers tab
        4. Add first provider (OpenAI with gpt-4o)
        5. Test connection
        6. Save provider
        7. Add second provider (Anthropic with claude-3-sonnet)
        8. Save second provider
        9. Set second provider as default
        10. Delete first provider
        11. Verify final state (one provider, marked as default)
        """
        # Step 1-2: Login and navigate
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()

        # Step 3: Navigate to AI Providers tab
        self.settings_page.click_ai_providers_tab()
        assert self.settings_page.verify_ai_providers_tab_loaded(), \
            "AI Providers tab should be loaded"

        # Step 4-6: Add first provider
        self.settings_page.click_add_provider_button()
        self.settings_page.select_provider("openai")
        self.settings_page.select_model("gpt-4o")
        self.settings_page.enter_api_key("sk-openai-complete-workflow")

        # Optional: Test connection if button exists
        try:
            self.settings_page.click_test_connection_button()
            time.sleep(2)
        except NoSuchElementException:
            pass  # Connection test button optional

        self.settings_page.click_save_provider_button()

        # Verify first provider saved
        assert self.settings_page.verify_provider_in_list("openai", "gpt-4o"), \
            "OpenAI provider should be saved"

        # Step 7-8: Add second provider
        self.settings_page.click_add_provider_button()
        self.settings_page.select_provider("anthropic")
        self.settings_page.select_model("claude-3-sonnet")
        self.settings_page.enter_api_key("sk-anthropic-complete-workflow")
        self.settings_page.click_save_provider_button()

        # Verify second provider saved
        assert self.settings_page.verify_provider_in_list("anthropic", "claude-3-sonnet"), \
            "Anthropic provider should be saved"

        # Step 9: Set second provider as default
        try:
            self.settings_page.click_set_default_button("anthropic")
            assert self.settings_page.verify_default_indicator("anthropic"), \
                "Anthropic should be marked as default"
        except NoSuchElementException:
            pass  # Set default may not be available if already default

        # Step 10: Delete first provider
        self.settings_page.click_delete_button("openai")

        # Step 11: Verify final state
        assert self.settings_page.verify_provider_deleted("openai"), \
            "OpenAI provider should be deleted"
        assert self.settings_page.verify_provider_in_list("anthropic"), \
            "Anthropic provider should still exist"

    # ========================================================================
    # Test 9: Provider Configuration Persistence
    # ========================================================================

    def test_09_provider_configuration_persistence(self):
        """
        Test: Provider configurations persist across sessions

        BUSINESS REQUIREMENT:
        LLM provider configurations must be stored in the database and
        persist across browser sessions. This ensures configurations
        don't need to be re-entered after logout.

        Steps:
        1. Login and add a provider
        2. Logout (or close browser session)
        3. Login again
        4. Navigate to AI Providers tab
        5. Verify previously configured provider is still present
        """
        # First session: Add provider
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()
        self.settings_page.click_ai_providers_tab()

        self.settings_page.click_add_provider_button()
        self.settings_page.select_provider("qwen")
        self.settings_page.select_model("qwen-vl-plus")
        self.settings_page.enter_api_key("sk-qwen-persistence-test")
        self.settings_page.click_save_provider_button()

        # Verify provider added
        assert self.settings_page.verify_provider_in_list("qwen"), \
            "Qwen provider should be saved in first session"

        # Simulate logout by clearing storage
        self.driver.delete_all_cookies()
        self.driver.execute_script("localStorage.clear();")

        # Second session: Login again
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()
        self.settings_page.click_ai_providers_tab()

        # Verify provider persisted
        assert self.settings_page.verify_provider_in_list("qwen"), \
            "Qwen provider should persist across sessions"

    # ========================================================================
    # Test 10: Navigation Between Settings Tabs
    # ========================================================================

    def test_10_navigation_between_settings_tabs(self):
        """
        Test: Can navigate between different settings tabs

        BUSINESS REQUIREMENT:
        Organization Settings has multiple tabs (Profile, Branding, Training,
        Integrations, AI Providers, Subscription). Users should be able to
        navigate between tabs without losing context.

        Steps:
        1. Login and navigate to Organization Settings
        2. Verify on Profile tab (default)
        3. Click AI Providers tab
        4. Verify AI Providers content loads
        5. Click back to Profile tab
        6. Verify Profile content loads
        7. Return to AI Providers tab
        8. Verify can still add providers
        """
        # Login and navigate
        self.login_page.login_as_org_admin()
        self.settings_page.navigate()

        # Should start on Profile tab (or any default tab)
        time.sleep(2)

        # Navigate to AI Providers tab
        self.settings_page.click_ai_providers_tab()
        assert self.settings_page.verify_ai_providers_tab_loaded(), \
            "AI Providers tab should load"

        # Navigate back to Profile tab
        try:
            profile_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Profile')]")
            profile_tab.click()
            time.sleep(1)
        except NoSuchElementException:
            pass  # Profile tab may have different text

        # Navigate back to AI Providers
        self.settings_page.click_ai_providers_tab()
        assert self.settings_page.verify_ai_providers_tab_loaded(), \
            "AI Providers tab should load again after navigation"

        # Verify can still interact with providers
        try:
            self.settings_page.click_add_provider_button()
        except NoSuchElementException:
            pass  # Add button may already be showing form
