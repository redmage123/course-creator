"""
Login Page Object

Encapsulates interactions with the login page for true E2E testing.
"""

import logging
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from tests.e2e.selenium_base import SeleniumConfig, BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """
    Page object for the login page.

    Provides methods for:
    - Navigating to login
    - Entering credentials
    - Submitting login form
    - Checking for errors
    - Verifying successful login
    """

    # Locators
    EMAIL_INPUT = (By.NAME, "email")
    USERNAME_INPUT = (By.NAME, "username")
    PASSWORD_INPUT = (By.NAME, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message, .alert-error, [role='alert']")
    FORGOT_PASSWORD_LINK = (By.LINK_TEXT, "Forgot Password")

    # Alternative locators - ordered by likelihood of matching
    # (Most common/working selectors first to avoid timeout delays)
    EMAIL_INPUT_ALTERNATIVES = [
        (By.CSS_SELECTOR, "input[placeholder*='example.com']"),  # Current React app
        (By.CSS_SELECTOR, "input[placeholder*='username']"),
        (By.CSS_SELECTOR, "form input[type='text']"),  # First text input in form
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.NAME, "email"),
        (By.NAME, "username"),
        (By.ID, "email"),
        (By.ID, "username"),
    ]

    PASSWORD_INPUT_ALTERNATIVES = [
        (By.CSS_SELECTOR, "input[type='password']"),  # Most reliable
        (By.NAME, "password"),
        (By.ID, "password"),
    ]

    LOGIN_BUTTON_ALTERNATIVES = [
        (By.XPATH, "//button[text()='Sign In']"),  # Current React app
        (By.XPATH, "//button[contains(text(), 'Sign In')]"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[contains(text(), 'Login')]"),
        (By.XPATH, "//button[contains(text(), 'Sign in')]"),
        (By.XPATH, "//button[contains(text(), 'Log in')]"),
    ]

    def __init__(self, driver: WebDriver, config: SeleniumConfig):
        """Initialize login page object."""
        super().__init__(driver, config)
        self.url = f"{self.base_url}/login"

    def navigate(self) -> "LoginPage":
        """
        Navigate to the login page.

        Returns:
            Self for method chaining
        """
        logger.info(f"Navigating to login page: {self.url}")
        self.driver.get(self.url)
        self._wait_for_page_ready()
        return self

    def _wait_for_page_ready(self) -> None:
        """Wait for login page to be fully loaded."""
        try:
            WebDriverWait(self.driver, self.config.explicit_wait).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # Wait for at least one of the input fields
            for selector in self.EMAIL_INPUT_ALTERNATIVES:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(selector)
                    )
                    return
                except TimeoutException:
                    continue
        except TimeoutException:
            self.take_screenshot("login_page_not_ready")
            raise

    def enter_email(self, email: str) -> "LoginPage":
        """
        Enter email/username in the login form.

        Args:
            email: Email or username to enter

        Returns:
            Self for method chaining
        """
        for selector in self.EMAIL_INPUT_ALTERNATIVES:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed():
                    element.clear()
                    element.send_keys(email)
                    logger.debug(f"Entered email using selector: {selector}")
                    return self
            except:
                continue

        raise TimeoutException("Could not find email/username input field")

    def enter_password(self, password: str) -> "LoginPage":
        """
        Enter password in the login form.

        Args:
            password: Password to enter

        Returns:
            Self for method chaining
        """
        for selector in self.PASSWORD_INPUT_ALTERNATIVES:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed():
                    element.clear()
                    element.send_keys(password)
                    logger.debug(f"Entered password using selector: {selector}")
                    return self
            except:
                continue

        raise TimeoutException("Could not find password input field")

    def click_login(self) -> None:
        """
        Click the login button.

        This submits the login form and waits for navigation.
        """
        for selector in self.LOGIN_BUTTON_ALTERNATIVES:
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(selector)
                )
                if element.is_displayed():
                    element.click()
                    logger.debug(f"Clicked login button using selector: {selector}")
                    return
            except:
                continue

        raise TimeoutException("Could not find login button")

    def login(self, email: str, password: str, timeout: int = 30) -> bool:
        """
        Complete login flow.

        Args:
            email: Email/username
            password: Password
            timeout: Maximum wait time for login completion

        Returns:
            True if login successful (redirected from login page)
        """
        self.navigate()
        self._handle_privacy_modal()
        self.enter_email(email)
        self.enter_password(password)
        self.click_login()

        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: '/login' not in d.current_url.lower()
            )
            logger.info(f"Login successful, redirected to: {self.driver.current_url}")
            return True
        except TimeoutException:
            error = self.get_error_message()
            if error:
                logger.error(f"Login failed with error: {error}")
            else:
                logger.error("Login failed - still on login page")
            self.take_screenshot("login_failed")
            return False

    def get_error_message(self) -> Optional[str]:
        """
        Get any error message displayed on the login page.

        Returns:
            Error message text or None if no error
        """
        error_selectors = [
            (By.CSS_SELECTOR, ".error-message"),
            (By.CSS_SELECTOR, ".alert-error"),
            (By.CSS_SELECTOR, ".alert-danger"),
            (By.CSS_SELECTOR, "[role='alert']"),
            (By.CSS_SELECTOR, ".form-error"),
            (By.CSS_SELECTOR, ".login-error"),
        ]

        for selector in error_selectors:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed() and element.text.strip():
                    return element.text.strip()
            except:
                continue

        return None

    def is_on_login_page(self) -> bool:
        """Check if currently on the login page."""
        return '/login' in self.driver.current_url.lower()

    def click_forgot_password(self) -> None:
        """Click the forgot password link."""
        self.click_element(*self.FORGOT_PASSWORD_LINK)

    def _handle_privacy_modal(self) -> None:
        """Handle privacy/cookie consent modal if present."""
        try:
            accept_buttons = [
                (By.XPATH, "//button[contains(text(), 'Accept')]"),
                (By.XPATH, "//button[contains(text(), 'Accept All')]"),
                (By.CSS_SELECTOR, "[data-testid='accept-cookies']"),
            ]

            for selector in accept_buttons:
                try:
                    button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    if button.is_displayed():
                        button.click()
                        import time
                        time.sleep(0.5)
                        return
                except:
                    pass
        except:
            pass

    def wait_for_redirect_to(self, url_fragment: str, timeout: int = 30) -> bool:
        """
        Wait for redirect to a specific URL.

        Args:
            url_fragment: URL fragment to wait for
            timeout: Maximum wait time

        Returns:
            True if redirected to URL containing fragment
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.url_contains(url_fragment)
            )
            return True
        except TimeoutException:
            return False
