"""
Selenium Base Classes for E2E Testing

Provides base classes and utilities for Selenium-based end-to-end testing
with Chrome driver support and best practices implementation.

BUSINESS CONTEXT:
E2E tests validate complete user workflows from browser interaction through
backend processing, ensuring the platform works correctly for real users.

TECHNICAL IMPLEMENTATION:
- Automatic ChromeDriver management via webdriver-manager
- Page Object Model (POM) pattern for maintainability
- Explicit waits for reliable tests
- Screenshot capture on failures
- Headless and headed mode support
"""

import os
import time
import logging
from datetime import datetime
from typing import Optional, List, Callable
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

logger = logging.getLogger(__name__)

# Import video recorder
try:
    from tests.e2e.video_recorder import VideoRecorder, FrameCaptureThread
    VIDEO_RECORDING_AVAILABLE = True
except ImportError:
    VIDEO_RECORDING_AVAILABLE = False
    logger.warning("Video recording not available - install opencv-python to enable")


class SeleniumConfig:
    """
    Configuration for Selenium testing environment.

    DESIGN PATTERN: Configuration Object
    Centralizes all Selenium-related configuration for easy management.
    """

    def __init__(self):
        # Determine base URL based on whether we're using Selenium Grid (Docker)
        # When using SELENIUM_REMOTE, we need to use Docker network hostname
        selenium_remote = os.getenv('SELENIUM_REMOTE')
        if selenium_remote and os.getenv('TEST_BASE_URL_DOCKER'):
            # Use Docker network URL (e.g., https://frontend:3000)
            self.base_url = os.getenv('TEST_BASE_URL_DOCKER')
        elif os.getenv('TEST_BASE_URL'):
            # Use explicitly configured URL
            self.base_url = os.getenv('TEST_BASE_URL')
        elif selenium_remote:
            # Default to Docker network hostname when using Selenium Grid
            self.base_url = 'https://frontend:3000'
        else:
            # Default to localhost for local testing
            self.base_url = 'https://localhost:3000'

        self.headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        self.screenshot_dir = os.getenv('SCREENSHOT_DIR', 'tests/reports/screenshots')
        self.video_dir = os.getenv('VIDEO_DIR', 'tests/reports/videos')
        self.record_video = os.getenv('RECORD_VIDEO', 'false').lower() == 'true'
        self.video_fps = int(os.getenv('VIDEO_FPS', '5'))
        self.implicit_wait = int(os.getenv('IMPLICIT_WAIT', '20'))
        self.explicit_wait = int(os.getenv('EXPLICIT_WAIT', '45'))
        self.window_width = int(os.getenv('WINDOW_WIDTH', '1920'))
        self.window_height = int(os.getenv('WINDOW_HEIGHT', '1080'))

        # Auto-detect Chrome/Chromium binary (only for local execution, not remote Selenium Grid)
        selenium_remote = os.getenv('SELENIUM_REMOTE')
        chrome_binary = os.getenv('CHROME_BINARY', None)

        # Skip binary detection when using remote Selenium Grid
        if not selenium_remote and not chrome_binary:
            # Check for snap chromium
            if os.path.exists('/snap/bin/chromium'):
                chrome_binary = '/snap/bin/chromium'
            # Check for google-chrome
            elif os.path.exists('/usr/bin/google-chrome'):
                chrome_binary = '/usr/bin/google-chrome'
            # Check for chromium-browser
            elif os.path.exists('/usr/bin/chromium-browser'):
                chrome_binary = '/usr/bin/chromium-browser'

        self.chrome_binary = chrome_binary
        self.disable_gpu = os.getenv('DISABLE_GPU', 'true').lower() == 'true'
        self.no_sandbox = os.getenv('NO_SANDBOX', 'true').lower() == 'true'

        # Create screenshot and video directories if they don't exist
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)


class ChromeDriverSetup:
    """
    Manages Chrome driver setup and configuration.

    BUSINESS REQUIREMENT:
    Provides consistent Chrome driver configuration across all E2E tests
    with automatic driver management and optimization for CI/CD environments.

    TECHNICAL FEATURES:
    - Automatic ChromeDriver installation via webdriver-manager
    - Headless mode for CI/CD pipelines
    - SSL certificate handling for HTTPS testing
    - Performance optimizations
    - Docker/container support
    """

    @staticmethod
    def create_chrome_options(config: SeleniumConfig) -> Options:
        """
        Create Chrome options with best practices configuration.

        Args:
            config: Selenium configuration object

        Returns:
            Configured Chrome options
        """
        options = Options()

        # Headless mode for CI/CD
        if config.headless:
            options.add_argument('--headless=new')  # New headless mode (Chrome 109+)
            logger.info("Running Chrome in headless mode")

        # Window size (important for responsive testing)
        options.add_argument(f'--window-size={config.window_width},{config.window_height}')

        # Performance and stability options
        options.add_argument('--no-sandbox')  # Required for Docker/CI
        options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
        options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration

        # Additional options for snap chromium stability
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--remote-debugging-port=0')  # Auto-assign random port for parallel tests
        options.add_argument('--disable-software-rasterizer')

        # Additional stability options for renderer connection issues
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--force-device-scale-factor=1')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-web-security')  # For CORS in local testing
        options.add_argument('--metrics-recording-only')
        options.add_argument('--mute-audio')
        options.add_argument('--disable-component-extensions-with-background-pages')

        # SSL/Security options for HTTPS testing
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-insecure-localhost')
        options.add_argument('--ignore-ssl-errors=yes')

        # Disable unnecessary features for testing
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-blink-features=AutomationControlled')  # Anti-detection

        # Logging
        options.add_argument('--log-level=3')  # Suppress verbose logging

        # User agent (optional - for specific testing scenarios)
        # options.add_argument('--user-agent=Your Custom User Agent')

        # Chrome binary path (if specified)
        # Skip setting binary_location when using remote Selenium Grid (Docker)
        # because the host's Chrome path doesn't exist in the Grid container
        selenium_remote = os.getenv('SELENIUM_REMOTE')
        if config.chrome_binary and not selenium_remote:
            options.binary_location = config.chrome_binary

        # Set unique user data directory for each session
        # DISABLED: Causing conflicts with pytest-selenium
        # import tempfile
        # user_data_dir = tempfile.mkdtemp(prefix="chrome_test_")
        # options.add_argument(f'--user-data-dir={user_data_dir}')

        # Enable downloads (useful for testing file downloads)
        prefs = {
            "download.default_directory": "/tmp/selenium_downloads",
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        # Remove "Chrome is being controlled by automated test software" banner
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Enable browser console logging for error detection
        # CRITICAL: Allows tests to check for JavaScript errors, API failures, CORS issues
        # User directive: "always have the agent check the console for errors when testing"
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        return options

    @staticmethod
    def create_driver(config: SeleniumConfig) -> webdriver.Chrome:
        """
        Create and configure Chrome WebDriver instance.

        Args:
            config: Selenium configuration object

        Returns:
            Configured Chrome WebDriver

        AUTOMATIC DRIVER MANAGEMENT:
        Uses webdriver-manager to automatically download and manage
        ChromeDriver versions matching the installed Chrome browser.

        DOCKER SELENIUM GRID SUPPORT:
        Set SELENIUM_REMOTE=http://localhost:4444 to use Docker Selenium Grid
        for stable Chrome 119 instead of local Chrome 141+.
        """
        try:
            # Create Chrome options
            options = ChromeDriverSetup.create_chrome_options(config)

            # Check if using remote Selenium Grid (Docker)
            selenium_remote = os.getenv('SELENIUM_REMOTE')

            if selenium_remote:
                # Use Docker Selenium Grid for stable Chrome 119
                logger.info(f"Using remote Selenium Grid: {selenium_remote}")
                driver = webdriver.Remote(
                    command_executor=selenium_remote,
                    options=options
                )
                logger.info(f"Remote Chrome WebDriver initialized (Grid version: {driver.capabilities.get('browserVersion', 'unknown')})")
            else:
                # Use local Chrome with webdriver-manager
                chrome_type = ChromeType.CHROMIUM if config.chrome_binary == '/snap/bin/chromium' else ChromeType.GOOGLE
                service = Service(ChromeDriverManager(chrome_type=chrome_type).install())
                driver = webdriver.Chrome(service=service, options=options)
                logger.info(f"Local Chrome WebDriver initialized (version: {driver.capabilities['browserVersion']})")

            # Set implicit wait
            driver.implicitly_wait(config.implicit_wait)

            # Maximize window (or set specific size)
            driver.set_window_size(config.window_width, config.window_height)

            return driver

        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise


class BasePage:
    """
    Base Page Object Model (POM) class.

    DESIGN PATTERN: Page Object Model
    Encapsulates page-specific elements and interactions for maintainability.

    RESPONSIBILITIES:
    - Common page operations (navigation, waiting, etc.)
    - Element locations and interaction methods
    - Screenshot capture on errors
    - Explicit wait utilities
    """

    def __init__(self, driver: webdriver.Chrome, config: SeleniumConfig):
        """
        Initialize base page.

        Args:
            driver: Chrome WebDriver instance
            config: Selenium configuration
        """
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, config.explicit_wait)
        self.base_url = config.base_url

    def navigate_to(self, path: str = "") -> None:
        """
        Navigate to a specific path on the base URL.

        Args:
            path: URL path to navigate to (relative to base_url)
        """
        url = f"{self.base_url}{path}"
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)

    def find_element(self, by: By, value: str, timeout: Optional[int] = None) -> WebElement:
        """
        Find element with explicit wait.

        Args:
            by: Selenium By locator strategy
            value: Locator value
            timeout: Optional custom timeout (uses config default if not specified)

        Returns:
            WebElement if found

        Raises:
            TimeoutException: If element not found within timeout
        """
        wait_time = timeout or self.config.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.take_screenshot(f"element_not_found_{value}")
            raise

    def find_elements(self, by: By, value: str) -> List[WebElement]:
        """
        Find multiple elements.

        Args:
            by: Selenium By locator strategy
            value: Locator value

        Returns:
            List of WebElements
        """
        return self.driver.find_elements(by, value)

    def click_element(self, by: By, value: str, timeout: Optional[int] = None) -> None:
        """
        Click element with explicit wait for clickability.

        Args:
            by: Selenium By locator strategy
            value: Locator value
            timeout: Optional custom timeout
        """
        wait_time = timeout or self.config.explicit_wait
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            logger.debug(f"Clicked element: {value}")
        except TimeoutException:
            self.take_screenshot(f"element_not_clickable_{value}")
            raise

    def enter_text(self, by: By, value: str, text: str, clear_first: bool = True) -> None:
        """
        Enter text into input field.

        Args:
            by: Selenium By locator strategy
            value: Locator value
            text: Text to enter
            clear_first: Whether to clear existing text first
        """
        element = self.find_element(by, value)
        if clear_first:
            element.clear()
        element.send_keys(text)
        logger.debug(f"Entered text into element: {value}")

    def get_text(self, by: By, value: str) -> str:
        """
        Get text content of element.

        Args:
            by: Selenium By locator strategy
            value: Locator value

        Returns:
            Element text content
        """
        element = self.find_element(by, value)
        return element.text

    def is_element_present(self, by: By, value: str, timeout: int = 5) -> bool:
        """
        Check if element is present on page.

        Args:
            by: Selenium By locator strategy
            value: Locator value
            timeout: Wait timeout in seconds

        Returns:
            True if element present, False otherwise
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            return False

    def wait_for_element_visible(self, by: By, value: str, timeout: Optional[int] = None) -> WebElement:
        """
        Wait for element to be visible.

        Args:
            by: Selenium By locator strategy
            value: Locator value
            timeout: Optional custom timeout

        Returns:
            Visible WebElement
        """
        wait_time = timeout or self.config.explicit_wait
        return WebDriverWait(self.driver, wait_time).until(
            EC.visibility_of_element_located((by, value))
        )

    def wait_for_url_contains(self, url_fragment: str, timeout: Optional[int] = None) -> bool:
        """
        Wait for URL to contain specific fragment.

        Args:
            url_fragment: URL fragment to wait for
            timeout: Optional custom timeout

        Returns:
            True if URL contains fragment within timeout
        """
        wait_time = timeout or self.config.explicit_wait
        try:
            WebDriverWait(self.driver, wait_time).until(
                EC.url_contains(url_fragment)
            )
            return True
        except TimeoutException:
            return False

    def take_screenshot(self, name: str = None) -> str:
        """
        Take screenshot and save to configured directory.

        Args:
            name: Optional screenshot name (timestamp used if not provided)

        Returns:
            Path to saved screenshot
        """
        if name is None:
            name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filename = f"{name}.png"
        filepath = os.path.join(self.config.screenshot_dir, filename)

        try:
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    def execute_script(self, script: str, *args):
        """
        Execute JavaScript in browser context.

        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to script

        Returns:
            Script return value
        """
        return self.driver.execute_script(script, *args)

    def scroll_to_element(self, element: WebElement) -> None:
        """
        Scroll element into view.

        Args:
            element: WebElement to scroll to
        """
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # Brief pause for scroll animation

    def get_current_url(self) -> str:
        """Get current page URL."""
        return self.driver.current_url

    def get_page_title(self) -> str:
        """Get current page title."""
        return self.driver.title

    @contextmanager
    def switch_to_frame(self, frame_reference):
        """
        Context manager for switching to iframe.

        Args:
            frame_reference: Frame name, ID, index, or WebElement

        Usage:
            with page.switch_to_frame('myframe'):
                page.click_element(By.ID, 'button-in-frame')
        """
        try:
            self.driver.switch_to.frame(frame_reference)
            yield
        finally:
            self.driver.switch_to.default_content()


class BaseTest:
    """
    Base test class for Selenium E2E tests.

    DESIGN PATTERN: Test Fixture
    Provides common setup/teardown and utilities for all E2E tests.

    RESPONSIBILITIES:
    - WebDriver lifecycle management
    - Test configuration
    - Screenshot capture on failures
    - Cleanup and resource management
    """

    @classmethod
    def setup_class(cls):
        """
        Class-level setup.
        Called once before any tests in the class run.
        """
        cls.config = SeleniumConfig()
        logger.info(f"Test configuration loaded. Base URL: {cls.config.base_url}")

    def setup_method(self, method):
        """
        Method-level setup.
        Called before each test method.
        """
        self.config = SeleniumConfig()
        self.driver = ChromeDriverSetup.create_driver(self.config)
        self.test_name = method.__name__

        # Initialize video recorder if enabled
        self.video_recorder = None
        self.frame_capturer = None
        if self.config.record_video and VIDEO_RECORDING_AVAILABLE:
            self.video_recorder = VideoRecorder(
                self.test_name,
                output_dir=self.config.video_dir,
                fps=self.config.video_fps,
                resolution=(self.config.window_width, self.config.window_height)
            )
            self.video_recorder.start()
            logger.info(f"Video recording enabled for test: {self.test_name}")

        logger.info(f"Starting test: {self.test_name}")

    def teardown_method(self, method):
        """
        Method-level teardown.
        Called after each test method.
        """
        if hasattr(self, 'driver') and self.driver:
            # Take final screenshot
            if hasattr(method, '__self__'):
                self.take_screenshot(f"{self.test_name}_final")

            # Stop video recording if enabled
            if self.video_recorder:
                # Capture final frame
                self.capture_video_frame()
                video_path = self.video_recorder.stop()
                if video_path:
                    logger.info(f"Video saved: {video_path}")

            # Close browser
            try:
                self.driver.quit()
                logger.info(f"Completed test: {self.test_name}")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")

    def take_screenshot(self, name: str = None) -> str:
        """
        Take screenshot with test context.

        Args:
            name: Optional screenshot name

        Returns:
            Path to saved screenshot
        """
        if name is None:
            name = f"{self.test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        page = BasePage(self.driver, self.config)
        return page.take_screenshot(name)

    def capture_video_frame(self):
        """
        Capture current frame for video recording

        Call this method after important test actions to add frames to video
        """
        if self.video_recorder and VIDEO_RECORDING_AVAILABLE:
            try:
                self.video_recorder.capture_frame_from_driver(self.driver)
            except Exception as e:
                logger.warning(f"Failed to capture video frame: {e}")

    def start_continuous_recording(self, interval: float = 0.2):
        """
        Start continuous video frame capture in background thread

        Args:
            interval: Seconds between frame captures (default 0.2 = 5 FPS)

        USAGE:
            self.start_continuous_recording()
            # ... perform test actions ...
            self.stop_continuous_recording()
        """
        if self.video_recorder and VIDEO_RECORDING_AVAILABLE:
            self.frame_capturer = FrameCaptureThread(
                self.driver,
                self.video_recorder,
                interval
            )
            self.frame_capturer.start()
            logger.info("Started continuous video frame capture")

    def stop_continuous_recording(self):
        """Stop continuous video frame capture"""
        if self.frame_capturer:
            self.frame_capturer.stop()
            logger.info("Stopped continuous video frame capture")

    def wait_for_element(self, locator, timeout=None):
        """Wait for element to be present."""
        timeout = timeout or self.config.explicit_wait
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_elements(self, locator, timeout=None):
        """Wait for elements to be present."""
        timeout = timeout or self.config.explicit_wait
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located(locator)
        )
        return self.driver.find_elements(*locator)

    def click_element(self, locator, timeout=None):
        """Click element with explicit wait."""
        timeout = timeout or self.config.explicit_wait
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()

    def click_element_js(self, element):
        """Click element using JavaScript."""
        self.driver.execute_script("arguments[0].click();", element)

    def type_text(self, locator, text, clear_first=True):
        """Type text into input field."""
        element = self.wait_for_element(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)

    def select_dropdown_option(self, locator, value):
        """Select option from dropdown by value."""
        from selenium.webdriver.support.ui import Select
        element = self.wait_for_element(locator)
        select = Select(element)
        select.select_by_value(value)

    def wait_for_url_contains(self, url_fragment, timeout=None):
        """Wait for URL to contain fragment."""
        timeout = timeout or self.config.explicit_wait
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.url_contains(url_fragment)
            )
            return True
        except TimeoutException:
            return False
