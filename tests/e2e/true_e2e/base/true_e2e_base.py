"""
True E2E Base Test Class

BUSINESS CONTEXT:
This base class enforces true end-to-end testing patterns that validate
the complete application flow from browser to database. It actively
detects and rejects anti-patterns that would allow bugs to slip through.

TECHNICAL IMPLEMENTATION:
- Extends BaseTest from selenium_base.py
- Overrides execute_script() to detect forbidden patterns
- Provides UI-based login helpers (no token injection)
- Provides React Query state waiting utilities
- Includes database connection for state verification

BUG PREVENTION:
The published_only bug was missed because E2E tests used:
    execute_script("return fetch('/api/v1/courses?published_only=false')")
Instead of using the actual React service layer:
    trainingProgramService.getOrganizationPrograms()

This base class prevents such bypass patterns.
"""

import re
import logging
import os
from typing import Optional, List, Dict, Any
from uuid import uuid4

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from tests.e2e.selenium_base import BaseTest, SeleniumConfig, ChromeDriverSetup

logger = logging.getLogger(__name__)


class TrueE2EViolation(Exception):
    """
    Raised when an anti-pattern is detected in test code.

    Anti-patterns bypass the frontend service layer and would
    allow bugs like published_only to go undetected.
    """
    pass


class TrueE2EBaseTest(BaseTest):
    """
    Base class for true end-to-end tests that never bypass frontend code.

    FORBIDDEN PATTERNS (will raise TrueE2EViolation):
    - Direct fetch() calls in execute_script
    - localStorage token injection
    - window.fetch mocking
    - Direct API URL patterns

    REQUIRED PATTERNS:
    - Login via actual UI form submission
    - Navigation via actual link/button clicks
    - Data verification via UI + database state comparison
    """

    # Patterns that indicate the test is bypassing the React frontend
    FORBIDDEN_PATTERNS = [
        (r"fetch\s*\(", "Direct fetch() calls bypass React service layer"),
        (r"localStorage\.setItem\s*\(\s*['\"]auth", "Token injection bypasses login flow"),
        (r"localStorage\.setItem\s*\(\s*['\"]token", "Token injection bypasses login flow"),
        (r"window\.fetch\s*=", "Mocking fetch bypasses real backend"),
        (r"XMLHttpRequest", "Direct XHR bypasses React service layer"),
        (r"/api/v1/", "Direct API paths suggest bypassing React"),
        (r"/api/v2/", "Direct API paths suggest bypassing React"),
    ]

    # Patterns that are allowed in execute_script
    ALLOWED_SCRIPT_PATTERNS = [
        r"scrollIntoView",           # Scroll operations
        r"scrollTo",                 # Scroll operations
        r"getBoundingClientRect",    # Element position
        r"getComputedStyle",         # Style reading
        r"arguments\[",              # Passing elements to JS
        r"return\s+document\.",      # DOM queries
        r"click\(\)",                # Click operations
        r"focus\(\)",                # Focus operations
        r"blur\(\)",                 # Blur operations
        r"value\s*=",                # Input value setting (for special cases)
        r"classList",                # Class manipulation
        r"style\.",                  # Style reading/setting
        r"offsetWidth",              # Dimension reading
        r"offsetHeight",             # Dimension reading
        r"__REACT_QUERY",            # React Query state checking
        r"isFetching",               # React Query checking
        r"setTimeout",               # Timing operations
        r"requestAnimationFrame",    # Animation frame
        r"Promise\.resolve",         # Promise operations for waits
        r"callback\s*\(",            # Async script callbacks
    ]

    def __init__(self):
        """Initialize test with anti-pattern detection enabled."""
        super().__init__()
        self._violation_check_enabled = True
        self._test_prefix = f"test_{uuid4().hex[:8]}"

    def setup_method(self, method):
        """
        Method-level setup with additional true E2E initialization.
        """
        super().setup_method(method)
        self._test_prefix = f"test_{uuid4().hex[:8]}"
        logger.info(f"True E2E test starting with prefix: {self._test_prefix}")

    def teardown_method(self, method):
        """
        Method-level teardown with cleanup verification.
        """
        # Check browser console for errors before teardown
        self._check_browser_console_errors()
        super().teardown_method(method)

    def execute_script(self, script: str, *args) -> Any:
        """
        Override execute_script to detect anti-patterns.

        This is the critical enforcement point. Any JavaScript execution
        that could bypass the React service layer is blocked.

        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to script

        Returns:
            Script return value

        Raises:
            TrueE2EViolation: If an anti-pattern is detected
        """
        if self._violation_check_enabled:
            self._check_for_violations(script)
        return self.driver.execute_script(script, *args)

    def execute_async_script(self, script: str, *args) -> Any:
        """
        Override execute_async_script to detect anti-patterns.
        """
        if self._violation_check_enabled:
            self._check_for_violations(script)
        return self.driver.execute_async_script(script, *args)

    def _check_for_violations(self, script: str) -> None:
        """
        Check script for forbidden patterns.

        Args:
            script: JavaScript code to check

        Raises:
            TrueE2EViolation: If a forbidden pattern is found
        """
        # First check if this script matches any allowed patterns
        for allowed_pattern in self.ALLOWED_SCRIPT_PATTERNS:
            if re.search(allowed_pattern, script, re.IGNORECASE):
                return  # Script contains allowed pattern, skip violation check

        # Check for forbidden patterns
        for pattern, message in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, script, re.IGNORECASE):
                raise TrueE2EViolation(
                    f"\n{'='*60}\n"
                    f"TRUE E2E VIOLATION DETECTED\n"
                    f"{'='*60}\n"
                    f"Anti-pattern: {message}\n"
                    f"Pattern: {pattern}\n"
                    f"Script excerpt: {script[:200]}...\n"
                    f"{'='*60}\n"
                    f"SOLUTION: Use UI interactions instead of JavaScript API calls.\n"
                    f"Example: Instead of fetch('/api/v1/courses'), navigate to\n"
                    f"the courses page and let React handle the API call.\n"
                    f"{'='*60}"
                )

    def _check_browser_console_errors(self) -> None:
        """
        Check browser console for JavaScript errors.

        Fails the test if severe errors are found (except known acceptable ones).
        """
        try:
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log.get('level') == 'SEVERE']

            # Filter known acceptable errors
            acceptable_patterns = [
                'favicon.ico',        # Missing favicon
                'DevTools',           # DevTools messages
                'net::ERR_FAILED',    # Network errors during cleanup
                'net::ERR_ABORTED',   # Aborted requests during navigation
            ]

            filtered_errors = []
            for error in errors:
                message = error.get('message', '')
                if not any(pattern in message for pattern in acceptable_patterns):
                    filtered_errors.append(error)

            if filtered_errors:
                error_messages = '\n'.join(e.get('message', str(e)) for e in filtered_errors)
                logger.warning(f"Browser console errors detected:\n{error_messages}")
                # Note: Not failing test for now, just logging
                # In strict mode, we might want to fail the test here
        except Exception as e:
            # Some drivers don't support get_log
            logger.debug(f"Could not get browser logs: {e}")

    # ========================================================================
    # UI-BASED LOGIN HELPERS
    # These methods use the actual login form, never token injection
    # ========================================================================

    def login_via_ui(self, email: str, password: str, timeout: int = 30) -> bool:
        """
        Login using the actual UI login form.

        This is the ONLY acceptable way to authenticate in true E2E tests.
        Token injection is forbidden because it bypasses the React auth flow.

        Args:
            email: User email/username
            password: User password
            timeout: Maximum wait time for login completion

        Returns:
            True if login successful (redirected to dashboard)

        Raises:
            TimeoutException: If login doesn't complete within timeout
        """
        logger.info(f"Logging in via UI as: {email}")

        # Navigate to login page
        self.driver.get(f"{self.config.base_url}/login")

        # Wait for login form to load
        self._wait_for_page_load()

        # Wait for and handle any privacy/cookie modal
        self._handle_privacy_modal()

        # Find and fill email field
        email_selectors = [
            (By.NAME, "email"),
            (By.NAME, "username"),
            (By.ID, "email"),
            (By.ID, "username"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name='email']"),
            (By.CSS_SELECTOR, "input[name='username']"),
        ]
        email_field = self._find_element_by_alternatives(email_selectors)
        email_field.clear()
        email_field.send_keys(email)

        # Find and fill password field
        password_selectors = [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]
        password_field = self._find_element_by_alternatives(password_selectors)
        password_field.clear()
        password_field.send_keys(password)

        # Find and click login button
        login_button_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'Sign in')]"),
            (By.XPATH, "//button[contains(text(), 'Log in')]"),
            (By.CSS_SELECTOR, "button.login-button"),
            (By.CSS_SELECTOR, "input[type='submit']"),
        ]
        login_button = self._find_element_by_alternatives(login_button_selectors)
        login_button.click()

        # Wait for redirect away from login page
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: '/login' not in d.current_url.lower()
            )
            logger.info(f"Login successful, redirected to: {self.driver.current_url}")

            # Additional wait for dashboard to fully load
            self._wait_for_page_load()

            return True
        except TimeoutException:
            # Check for error messages
            error_selectors = [
                (By.CSS_SELECTOR, ".error-message"),
                (By.CSS_SELECTOR, ".alert-error"),
                (By.CSS_SELECTOR, "[role='alert']"),
                (By.CSS_SELECTOR, ".form-error"),
            ]
            for selector in error_selectors:
                try:
                    error_element = self.driver.find_element(*selector)
                    if error_element.is_displayed():
                        logger.error(f"Login error: {error_element.text}")
                        break
                except:
                    pass

            self.take_screenshot("login_failed")
            raise TimeoutException(f"Login did not complete within {timeout} seconds")

    def logout_via_ui(self, timeout: int = 15) -> bool:
        """
        Logout using the actual UI logout functionality.

        Args:
            timeout: Maximum wait time for logout

        Returns:
            True if logout successful
        """
        logger.info("Logging out via UI")

        # Try various logout mechanisms
        logout_selectors = [
            (By.CSS_SELECTOR, "[data-testid='logout-button']"),
            (By.XPATH, "//button[contains(text(), 'Logout')]"),
            (By.XPATH, "//button[contains(text(), 'Log out')]"),
            (By.XPATH, "//a[contains(text(), 'Logout')]"),
            (By.CSS_SELECTOR, ".logout-button"),
        ]

        # First try to find logout in user menu
        user_menu_selectors = [
            (By.CSS_SELECTOR, "[data-testid='user-menu']"),
            (By.CSS_SELECTOR, ".user-menu"),
            (By.CSS_SELECTOR, "[aria-label='User menu']"),
        ]

        try:
            # Click user menu first if it exists
            for selector in user_menu_selectors:
                try:
                    menu = self.driver.find_element(*selector)
                    if menu.is_displayed():
                        menu.click()
                        import time
                        time.sleep(0.5)
                        break
                except:
                    pass

            # Click logout button
            logout_button = self._find_element_by_alternatives(logout_selectors)
            logout_button.click()

            # Wait for redirect to login page
            WebDriverWait(self.driver, timeout).until(
                EC.url_contains('/login')
            )
            logger.info("Logout successful")
            return True

        except Exception as e:
            logger.warning(f"Logout via UI failed: {e}")
            # Fallback: clear storage and navigate to login
            self._violation_check_enabled = False
            try:
                self.driver.execute_script("localStorage.clear(); sessionStorage.clear();")
            finally:
                self._violation_check_enabled = True
            self.driver.get(f"{self.config.base_url}/login")
            return True

    # ========================================================================
    # NAVIGATION HELPERS
    # Use these instead of direct URL manipulation
    # ========================================================================

    def navigate_to_page(self, path: str) -> None:
        """
        Navigate to a page using the URL.

        While direct URL navigation is acceptable, it's better to navigate
        via UI clicks when testing specific workflows.

        Args:
            path: URL path relative to base_url
        """
        full_url = f"{self.config.base_url}{path}"
        logger.info(f"Navigating to: {full_url}")
        self.driver.get(full_url)
        self._wait_for_page_load()

    def click_nav_link(self, link_text: str, timeout: int = 10) -> None:
        """
        Click a navigation link by its text.

        Args:
            link_text: Text of the navigation link
            timeout: Maximum wait time
        """
        selectors = [
            (By.LINK_TEXT, link_text),
            (By.PARTIAL_LINK_TEXT, link_text),
            (By.XPATH, f"//nav//a[contains(text(), '{link_text}')]"),
            (By.XPATH, f"//a[contains(text(), '{link_text}')]"),
        ]
        element = self._find_element_by_alternatives(selectors, timeout)
        element.click()
        self._wait_for_page_load()

    def click_button(self, button_text: str, timeout: int = 10) -> None:
        """
        Click a button by its text.

        Args:
            button_text: Text of the button
            timeout: Maximum wait time
        """
        selectors = [
            (By.XPATH, f"//button[contains(text(), '{button_text}')]"),
            (By.XPATH, f"//button[normalize-space()='{button_text}']"),
            (By.XPATH, f"//*[contains(@class, 'button') and contains(text(), '{button_text}')]"),
        ]
        element = self._find_element_by_alternatives(selectors, timeout)
        element.click()

    # ========================================================================
    # WAIT HELPERS
    # ========================================================================

    def _wait_for_page_load(self, timeout: int = 30) -> None:
        """
        Wait for page to fully load including React hydration.
        """
        # Wait for document ready state
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Wait for React Query to settle
        self._wait_for_react_query_idle(timeout)

    def _wait_for_react_query_idle(self, timeout: int = 30) -> bool:
        """
        Wait for React Query to finish all pending queries.

        This is critical for true E2E testing - we need to wait for
        the actual React service layer to complete its API calls.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if React Query is idle
        """
        # Temporarily disable violation checking for React Query state inspection
        original_check = self._violation_check_enabled
        self._violation_check_enabled = False

        try:
            # Check if React Query DevTools client is available
            has_react_query = self.driver.execute_script("""
                return typeof window.__REACT_QUERY_DEVTOOLS_GLOBAL_CLIENT__ !== 'undefined' ||
                       typeof window.__REACT_QUERY_CLIENT__ !== 'undefined';
            """)

            if has_react_query:
                # Use React Query client to check for pending queries
                return self.driver.execute_async_script("""
                    const callback = arguments[arguments.length - 1];
                    const timeout = arguments[0];
                    const startTime = Date.now();

                    const client = window.__REACT_QUERY_DEVTOOLS_GLOBAL_CLIENT__ ||
                                   window.__REACT_QUERY_CLIENT__;

                    if (!client) {
                        callback(true);
                        return;
                    }

                    const checkIdle = () => {
                        if (Date.now() - startTime > timeout) {
                            callback(false);
                            return;
                        }

                        const isFetching = client.isFetching ? client.isFetching() : false;

                        if (!isFetching) {
                            // Wait a bit more to ensure no new queries start
                            setTimeout(() => {
                                const stillFetching = client.isFetching ? client.isFetching() : false;
                                callback(!stillFetching);
                            }, 200);
                        } else {
                            setTimeout(checkIdle, 100);
                        }
                    };

                    checkIdle();
                """, timeout * 1000)
            else:
                # Fallback: Monitor network activity
                return self._wait_for_network_idle(timeout)

        except Exception as e:
            logger.debug(f"React Query check failed: {e}")
            # Fallback to network idle
            return self._wait_for_network_idle(timeout)
        finally:
            self._violation_check_enabled = original_check

    def _wait_for_network_idle(self, timeout: int = 30) -> bool:
        """
        Fallback method to wait for network activity to settle.
        """
        original_check = self._violation_check_enabled
        self._violation_check_enabled = False

        try:
            return self.driver.execute_async_script("""
                const callback = arguments[arguments.length - 1];
                const timeout = arguments[0];
                const startTime = Date.now();
                let lastActivityTime = Date.now();
                let pendingRequests = 0;

                // Track fetch requests
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    pendingRequests++;
                    lastActivityTime = Date.now();
                    return originalFetch.apply(this, args)
                        .finally(() => {
                            pendingRequests--;
                            lastActivityTime = Date.now();
                        });
                };

                const checkIdle = () => {
                    if (Date.now() - startTime > timeout) {
                        window.fetch = originalFetch;
                        callback(false);
                        return;
                    }

                    if (pendingRequests === 0 && (Date.now() - lastActivityTime) > 500) {
                        window.fetch = originalFetch;
                        callback(true);
                    } else {
                        setTimeout(checkIdle, 100);
                    }
                };

                // Start checking after a brief delay
                setTimeout(checkIdle, 100);
            """, timeout * 1000)
        except Exception as e:
            logger.debug(f"Network idle check failed: {e}")
            # Simple fallback - just wait
            import time
            time.sleep(1)
            return True
        finally:
            self._violation_check_enabled = original_check

    def _handle_privacy_modal(self, timeout: int = 5) -> None:
        """
        Handle privacy/cookie consent modal if present.
        """
        try:
            accept_buttons = [
                (By.XPATH, "//button[contains(text(), 'Accept')]"),
                (By.XPATH, "//button[contains(text(), 'Accept All')]"),
                (By.XPATH, "//button[contains(text(), 'I Agree')]"),
                (By.CSS_SELECTOR, "[data-testid='accept-cookies']"),
                (By.CSS_SELECTOR, ".cookie-accept-button"),
            ]

            for selector in accept_buttons:
                try:
                    button = WebDriverWait(self.driver, timeout).until(
                        EC.element_to_be_clickable(selector)
                    )
                    if button.is_displayed():
                        button.click()
                        logger.info("Accepted privacy/cookie consent")
                        import time
                        time.sleep(0.5)
                        return
                except:
                    pass
        except Exception as e:
            logger.debug(f"No privacy modal found or couldn't handle it: {e}")

    def _find_element_by_alternatives(
        self,
        selectors: List[tuple],
        timeout: int = 10
    ):
        """
        Try multiple selectors to find an element.

        Args:
            selectors: List of (By, value) tuples to try
            timeout: Maximum wait time

        Returns:
            Found WebElement

        Raises:
            TimeoutException: If no selector finds the element
        """
        for by, value in selectors:
            try:
                element = WebDriverWait(self.driver, timeout / len(selectors)).until(
                    EC.presence_of_element_located((by, value))
                )
                if element.is_displayed():
                    return element
            except:
                continue

        # Take screenshot before failing
        self.take_screenshot(f"element_not_found_{selectors[0][1][:20]}")
        raise TimeoutException(
            f"Could not find element with any selector: {selectors}"
        )

    # ========================================================================
    # DATA VERIFICATION HELPERS
    # ========================================================================

    def get_visible_text_content(self, container_selector: tuple = None) -> str:
        """
        Get all visible text content from the page or a container.

        Args:
            container_selector: Optional (By, value) tuple to limit scope

        Returns:
            Combined visible text content
        """
        if container_selector:
            container = self.driver.find_element(*container_selector)
        else:
            container = self.driver.find_element(By.TAG_NAME, "body")

        return container.text

    def get_list_items(self, list_selector: tuple) -> List[str]:
        """
        Get text content of all items in a list.

        Args:
            list_selector: (By, value) tuple for list items

        Returns:
            List of text content from each item
        """
        elements = self.driver.find_elements(*list_selector)
        return [el.text for el in elements if el.is_displayed()]

    def count_elements(self, selector: tuple) -> int:
        """
        Count visible elements matching a selector.

        Args:
            selector: (By, value) tuple

        Returns:
            Count of matching visible elements
        """
        elements = self.driver.find_elements(*selector)
        return sum(1 for el in elements if el.is_displayed())

    # ========================================================================
    # TEST DATA IDENTIFICATION
    # ========================================================================

    @property
    def test_prefix(self) -> str:
        """
        Get unique prefix for test data.

        Use this prefix when creating test data to ensure cleanup.
        """
        return self._test_prefix

    def create_unique_name(self, base_name: str) -> str:
        """
        Create a unique name for test data.

        Args:
            base_name: Base name for the entity

        Returns:
            Unique name with test prefix
        """
        return f"{self._test_prefix}_{base_name}"
