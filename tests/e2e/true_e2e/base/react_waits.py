"""
React Wait Helpers for True E2E Testing

BUSINESS CONTEXT:
React applications with data fetching libraries like React Query have
asynchronous state updates. True E2E tests must wait for these updates
to complete before asserting on UI state.

TECHNICAL IMPLEMENTATION:
- React Query state monitoring
- Network request tracking
- Loading state detection
- Animation completion waiting

These utilities ensure tests don't fail due to timing issues while
still testing the real React application behavior.
"""

import logging
import time
from typing import Optional, Callable, Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)


class ReactWaitHelpers:
    """
    Utilities for waiting on React application state.

    USAGE:
        waits = ReactWaitHelpers(driver)
        waits.wait_for_loading_complete()
        waits.wait_for_element_stable(locator)
    """

    # Common loading indicator selectors
    LOADING_INDICATORS = [
        (By.CSS_SELECTOR, "[data-testid='loading']"),
        (By.CSS_SELECTOR, "[data-testid='loading-spinner']"),
        (By.CSS_SELECTOR, ".loading"),
        (By.CSS_SELECTOR, ".loading-spinner"),
        (By.CSS_SELECTOR, ".spinner"),
        (By.CSS_SELECTOR, "[aria-label='Loading']"),
        (By.CSS_SELECTOR, ".MuiCircularProgress-root"),
        (By.CSS_SELECTOR, ".ant-spin"),
        (By.CSS_SELECTOR, "[role='progressbar']"),
    ]

    # Common skeleton loader selectors
    SKELETON_INDICATORS = [
        (By.CSS_SELECTOR, ".skeleton"),
        (By.CSS_SELECTOR, ".skeleton-loader"),
        (By.CSS_SELECTOR, "[data-testid='skeleton']"),
        (By.CSS_SELECTOR, ".MuiSkeleton-root"),
        (By.CSS_SELECTOR, ".ant-skeleton"),
    ]

    def __init__(self, driver: WebDriver):
        """
        Initialize wait helpers.

        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver

    def wait_for_loading_complete(self, timeout: int = 30) -> bool:
        """
        Wait for all loading indicators to disappear.

        This checks for common loading spinners, skeleton loaders,
        and other loading state indicators.

        NOTE: Temporarily disables implicit wait to avoid 20s delays
        when selectors don't match any elements.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if loading completed, False if timeout
        """
        start_time = time.time()

        # Save original implicit wait and disable it
        # This prevents 20s delays when selectors don't match
        original_implicit_wait = self.driver.timeouts.implicit_wait
        self.driver.implicitly_wait(0)

        try:
            while time.time() - start_time < timeout:
                loading_visible = False

                # Check loading spinners
                for selector in self.LOADING_INDICATORS:
                    try:
                        elements = self.driver.find_elements(*selector)
                        for el in elements:
                            if el.is_displayed():
                                loading_visible = True
                                break
                    except:
                        pass
                    if loading_visible:
                        break

                # Check skeleton loaders if no spinners
                if not loading_visible:
                    for selector in self.SKELETON_INDICATORS:
                        try:
                            elements = self.driver.find_elements(*selector)
                            for el in elements:
                                if el.is_displayed():
                                    loading_visible = True
                                    break
                        except:
                            pass
                        if loading_visible:
                            break

                if not loading_visible:
                    logger.debug("Loading complete - no loading indicators visible")
                    return True

                time.sleep(0.1)

            logger.warning(f"Loading did not complete within {timeout} seconds")
            return False
        finally:
            # Restore original implicit wait
            self.driver.implicitly_wait(original_implicit_wait)

    def wait_for_element_stable(
        self,
        locator: tuple,
        stability_time: float = 0.5,
        timeout: int = 10
    ) -> bool:
        """
        Wait for an element to become stable (stop changing).

        Useful for waiting for animations to complete or content
        to finish loading.

        Args:
            locator: (By, value) tuple for element
            stability_time: Time element must be unchanged
            timeout: Maximum wait time

        Returns:
            True if element became stable
        """
        start_time = time.time()
        last_state = None
        stable_since = None

        while time.time() - start_time < timeout:
            try:
                element = self.driver.find_element(*locator)
                current_state = (
                    element.location,
                    element.size,
                    element.text[:100] if element.text else "",
                    element.is_displayed(),
                )

                if current_state == last_state:
                    if stable_since is None:
                        stable_since = time.time()
                    elif time.time() - stable_since >= stability_time:
                        logger.debug(f"Element stable: {locator}")
                        return True
                else:
                    last_state = current_state
                    stable_since = None

            except Exception as e:
                last_state = None
                stable_since = None

            time.sleep(0.05)

        logger.warning(f"Element did not become stable: {locator}")
        return False

    def wait_for_text_present(
        self,
        text: str,
        container_locator: tuple = None,
        timeout: int = 10
    ) -> bool:
        """
        Wait for specific text to appear in the page or container.

        Args:
            text: Text to wait for
            container_locator: Optional container to search in
            timeout: Maximum wait time

        Returns:
            True if text found
        """
        try:
            if container_locator:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: text in d.find_element(*container_locator).text
                )
            else:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: text in d.page_source
                )
            return True
        except TimeoutException:
            return False

    def wait_for_text_absent(
        self,
        text: str,
        container_locator: tuple = None,
        timeout: int = 10
    ) -> bool:
        """
        Wait for specific text to disappear from the page or container.

        Args:
            text: Text to wait for removal
            container_locator: Optional container to search in
            timeout: Maximum wait time

        Returns:
            True if text disappeared
        """
        try:
            if container_locator:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: text not in d.find_element(*container_locator).text
                )
            else:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: text not in d.page_source
                )
            return True
        except TimeoutException:
            return False

    def wait_for_url_change(
        self,
        original_url: str,
        timeout: int = 10
    ) -> bool:
        """
        Wait for URL to change from original.

        Args:
            original_url: URL before the action
            timeout: Maximum wait time

        Returns:
            True if URL changed
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.current_url != original_url
            )
            return True
        except TimeoutException:
            return False

    def wait_for_element_count(
        self,
        locator: tuple,
        expected_count: int,
        comparison: str = "eq",
        timeout: int = 10
    ) -> bool:
        """
        Wait for a specific number of elements.

        Args:
            locator: (By, value) tuple
            expected_count: Expected number of elements
            comparison: "eq" (equal), "gt" (greater than), "lt" (less than)
            timeout: Maximum wait time

        Returns:
            True if condition met
        """
        def check_count(driver):
            elements = driver.find_elements(*locator)
            visible_count = sum(1 for el in elements if el.is_displayed())

            if comparison == "eq":
                return visible_count == expected_count
            elif comparison == "gt":
                return visible_count > expected_count
            elif comparison == "lt":
                return visible_count < expected_count
            elif comparison == "gte":
                return visible_count >= expected_count
            elif comparison == "lte":
                return visible_count <= expected_count
            return False

        try:
            WebDriverWait(self.driver, timeout).until(check_count)
            return True
        except TimeoutException:
            return False

    def wait_for_react_query_idle(self, timeout: int = 30) -> bool:
        """
        Wait for React Query to finish all pending queries.

        This is the preferred method for waiting on data fetching.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if React Query is idle
        """
        try:
            return self.driver.execute_async_script("""
                const callback = arguments[arguments.length - 1];
                const timeout = arguments[0];
                const startTime = Date.now();

                // Check for React Query client
                const client = window.__REACT_QUERY_DEVTOOLS_GLOBAL_CLIENT__ ||
                               window.__REACT_QUERY_CLIENT__;

                if (!client) {
                    // No React Query - wait for document ready
                    const checkReady = () => {
                        if (document.readyState === 'complete') {
                            setTimeout(() => callback(true), 200);
                        } else if (Date.now() - startTime > timeout) {
                            callback(false);
                        } else {
                            setTimeout(checkReady, 50);
                        }
                    };
                    checkReady();
                    return;
                }

                const checkIdle = () => {
                    if (Date.now() - startTime > timeout) {
                        callback(false);
                        return;
                    }

                    const isFetching = client.isFetching ? client.isFetching() : 0;

                    if (isFetching === 0) {
                        // Wait a bit more to ensure stability
                        setTimeout(() => {
                            const stillFetching = client.isFetching ? client.isFetching() : 0;
                            if (stillFetching === 0) {
                                callback(true);
                            } else {
                                setTimeout(checkIdle, 50);
                            }
                        }, 200);
                    } else {
                        setTimeout(checkIdle, 50);
                    }
                };

                checkIdle();
            """, timeout * 1000)
        except Exception as e:
            logger.debug(f"React Query idle check failed: {e}")
            # Fallback - wait for loading complete
            return self.wait_for_loading_complete(timeout)

    def wait_for_form_validation(self, timeout: int = 5) -> None:
        """
        Wait for form validation to complete.

        Forms often have debounced validation - this ensures
        validation messages have appeared before checking them.
        """
        time.sleep(0.3)  # Brief wait for debounce
        self.wait_for_loading_complete(timeout)

    def wait_for_toast_notification(
        self,
        expected_text: str = None,
        timeout: int = 10
    ) -> Optional[str]:
        """
        Wait for a toast notification to appear.

        Args:
            expected_text: Optional text the toast should contain
            timeout: Maximum wait time

        Returns:
            Toast message text, or None if not found
        """
        toast_selectors = [
            (By.CSS_SELECTOR, "[data-testid='toast']"),
            (By.CSS_SELECTOR, ".toast"),
            (By.CSS_SELECTOR, ".Toastify__toast"),
            (By.CSS_SELECTOR, ".notification"),
            (By.CSS_SELECTOR, ".MuiSnackbar-root"),
            (By.CSS_SELECTOR, "[role='alert']"),
            (By.CSS_SELECTOR, ".ant-notification"),
        ]

        start_time = time.time()

        # Disable implicit wait to avoid delays on unmatched selectors
        original_implicit_wait = self.driver.timeouts.implicit_wait
        self.driver.implicitly_wait(0)

        try:
            while time.time() - start_time < timeout:
                for selector in toast_selectors:
                    try:
                        elements = self.driver.find_elements(*selector)
                        for el in elements:
                            if el.is_displayed():
                                text = el.text
                                if expected_text is None or expected_text in text:
                                    logger.debug(f"Found toast: {text[:100]}")
                                    return text
                    except:
                        pass
                time.sleep(0.1)

            return None
        finally:
            self.driver.implicitly_wait(original_implicit_wait)

    def wait_for_modal_open(self, timeout: int = 10) -> bool:
        """
        Wait for a modal dialog to open.

        Returns:
            True if modal found and visible
        """
        modal_selectors = [
            (By.CSS_SELECTOR, "[role='dialog']"),
            (By.CSS_SELECTOR, ".modal"),
            (By.CSS_SELECTOR, ".modal-dialog"),
            (By.CSS_SELECTOR, ".MuiModal-root"),
            (By.CSS_SELECTOR, ".ant-modal"),
            (By.CSS_SELECTOR, "[data-testid='modal']"),
        ]

        start_time = time.time()

        # Disable implicit wait to avoid delays on unmatched selectors
        original_implicit_wait = self.driver.timeouts.implicit_wait
        self.driver.implicitly_wait(0)

        try:
            while time.time() - start_time < timeout:
                for selector in modal_selectors:
                    try:
                        elements = self.driver.find_elements(*selector)
                        for el in elements:
                            if el.is_displayed():
                                logger.debug("Modal opened")
                                return True
                    except:
                        pass
                time.sleep(0.1)

            return False
        finally:
            self.driver.implicitly_wait(original_implicit_wait)

    def wait_for_modal_close(self, timeout: int = 10) -> bool:
        """
        Wait for modal dialog to close.

        Returns:
            True if no modals visible
        """
        modal_selectors = [
            (By.CSS_SELECTOR, "[role='dialog']"),
            (By.CSS_SELECTOR, ".modal.show"),
            (By.CSS_SELECTOR, ".modal-dialog"),
            (By.CSS_SELECTOR, ".MuiModal-root"),
        ]

        start_time = time.time()

        # Disable implicit wait to avoid delays on unmatched selectors
        original_implicit_wait = self.driver.timeouts.implicit_wait
        self.driver.implicitly_wait(0)

        try:
            while time.time() - start_time < timeout:
                modal_visible = False
                for selector in modal_selectors:
                    try:
                        elements = self.driver.find_elements(*selector)
                        for el in elements:
                            if el.is_displayed():
                                modal_visible = True
                                break
                    except:
                        pass
                    if modal_visible:
                        break

                if not modal_visible:
                    logger.debug("Modal closed")
                    return True

                time.sleep(0.1)

            return False
        finally:
            self.driver.implicitly_wait(original_implicit_wait)

    def retry_until_success(
        self,
        action: Callable[[], Any],
        max_retries: int = 3,
        delay: float = 1.0,
        expected_exception: type = Exception
    ) -> Any:
        """
        Retry an action until it succeeds or max retries reached.

        Args:
            action: Callable to execute
            max_retries: Maximum number of attempts
            delay: Seconds between retries
            expected_exception: Exception type to catch and retry

        Returns:
            Result of successful action

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return action()
            except expected_exception as e:
                last_exception = e
                logger.debug(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)

        raise last_exception
