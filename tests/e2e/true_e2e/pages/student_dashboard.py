"""
Student Dashboard Page Object

Encapsulates interactions with the student dashboard for true E2E testing.
"""

import logging
from typing import List, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from tests.e2e.selenium_base import SeleniumConfig, BasePage
from tests.e2e.true_e2e.base.react_waits import ReactWaitHelpers

logger = logging.getLogger(__name__)


class StudentDashboard(BasePage):
    """
    Page object for the student dashboard.

    Provides methods for:
    - Viewing enrolled courses
    - Accessing course content
    - Viewing progress
    - Starting labs
    - Taking quizzes

    NOTE: CSS Modules are used in the frontend, so class names are hashed.
    We use robust selectors based on semantic structure rather than class names.
    """

    # Locators - using semantic structure instead of hashed class names
    DASHBOARD_TITLE = (By.CSS_SELECTOR, "h1, .dashboard-title, [data-testid='dashboard-title']")
    # Courses are displayed as links to /courses/{id}
    COURSE_LINKS = (By.CSS_SELECTOR, "a[href^='/courses/']")
    ENROLLED_COURSES = (By.XPATH, "//a[starts-with(@href, '/courses/')]/ancestor::div[contains(@class, 'card') or contains(@class, 'Card') or position()=1]")
    COURSE_TITLE = (By.CSS_SELECTOR, "a[href^='/courses/'], h3, h4")
    PROGRESS_BAR = (By.CSS_SELECTOR, "[role='progressbar'], progress, .progress-bar")
    START_COURSE_BUTTON = (By.XPATH, "//button[contains(text(), 'Start') or contains(text(), 'View')]")
    CONTINUE_COURSE_BUTTON = (By.XPATH, "//button[contains(text(), 'Continue')]")
    LAB_BUTTON = (By.XPATH, "//button[contains(text(), 'Lab') or contains(text(), 'Start Lab')]")
    QUIZ_BUTTON = (By.XPATH, "//button[contains(text(), 'Quiz') or contains(text(), 'Take Quiz')]")

    # Navigation
    NAV_MY_COURSES = (By.XPATH, "//a[contains(text(), 'My Courses') or contains(text(), 'Courses')]")
    NAV_PROGRESS = (By.XPATH, "//a[contains(text(), 'Progress')]")
    NAV_CERTIFICATES = (By.XPATH, "//a[contains(text(), 'Certificates')]")

    # Dashboard sections
    WELCOME_MESSAGE = (By.CSS_SELECTOR, "h1, h2, .welcome-message, [data-testid='welcome']")
    RECENT_ACTIVITY = (By.CSS_SELECTOR, ".recent-activity, [data-testid='recent-activity']")
    UPCOMING_DEADLINES = (By.CSS_SELECTOR, ".deadlines, [data-testid='deadlines']")

    def __init__(self, driver: WebDriver, config: SeleniumConfig):
        """Initialize student dashboard page object."""
        super().__init__(driver, config)
        self.waits = ReactWaitHelpers(driver)
        self.url = f"{self.base_url}/dashboard/student"

    def navigate(self) -> "StudentDashboard":
        """
        Navigate to the student dashboard.

        Returns:
            Self for method chaining
        """
        logger.info(f"Navigating to student dashboard: {self.url}")
        self.driver.get(self.url)
        self._wait_for_dashboard_ready()
        return self

    def _wait_for_dashboard_ready(self) -> None:
        """Wait for dashboard to be fully loaded."""
        self.waits.wait_for_loading_complete()
        self.waits.wait_for_react_query_idle()

    def is_on_dashboard(self) -> bool:
        """Check if currently on the student dashboard."""
        current_url = self.driver.current_url.lower()
        return 'dashboard' in current_url and 'student' in current_url

    def get_welcome_message(self) -> Optional[str]:
        """Get the welcome message text."""
        try:
            element = self.find_element(*self.WELCOME_MESSAGE)
            return element.text
        except TimeoutException:
            return None

    def get_enrolled_course_count(self) -> int:
        """
        Get the number of enrolled courses displayed.

        Returns:
            Count of course links visible on dashboard
        """
        self.waits.wait_for_loading_complete()
        # Use COURSE_LINKS selector which finds links to courses
        elements = self.find_elements(*self.COURSE_LINKS)
        visible_count = sum(1 for el in elements if el.is_displayed())
        logger.info(f"Found {visible_count} course links in UI")
        return visible_count

    def get_enrolled_course_titles(self) -> List[str]:
        """
        Get titles of all enrolled courses.

        Returns:
            List of course titles (from links to /courses/)
        """
        self.waits.wait_for_loading_complete()
        # Use COURSE_LINKS to find course links - their text is the title
        links = self.find_elements(*self.COURSE_LINKS)
        titles = []

        for link in links:
            if link.is_displayed():
                title = link.text.strip()
                if title:
                    titles.append(title)

        logger.info(f"Found course titles: {titles}")
        return titles

    def click_course(self, course_title: str) -> bool:
        """
        Click on a specific course card.

        Args:
            course_title: Title of course to click

        Returns:
            True if course was found and clicked
        """
        links = self.find_elements(*self.COURSE_LINKS)

        for link in links:
            if course_title in link.text:
                self.scroll_to_element(link)
                link.click()
                self.waits.wait_for_loading_complete()
                return True

        logger.warning(f"Course not found: {course_title}")
        return False

    def start_course(self, course_title: str) -> bool:
        """
        Start a specific course.

        Args:
            course_title: Title of course to start

        Returns:
            True if course was started
        """
        if self.click_course(course_title):
            try:
                start_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(self.START_COURSE_BUTTON)
                )
                start_button.click()
                self.waits.wait_for_loading_complete()
                return True
            except TimeoutException:
                # Maybe already started - look for continue button
                try:
                    continue_button = self.driver.find_element(*self.CONTINUE_COURSE_BUTTON)
                    continue_button.click()
                    self.waits.wait_for_loading_complete()
                    return True
                except:
                    pass

        return False

    def get_course_progress(self, course_title: str) -> Optional[int]:
        """
        Get progress percentage for a course.

        Args:
            course_title: Title of course

        Returns:
            Progress percentage (0-100) or None if not found
        """
        course_cards = self.find_elements(*self.ENROLLED_COURSES)

        for card in course_cards:
            if course_title in card.text:
                try:
                    progress_bar = card.find_element(*self.PROGRESS_BAR)
                    # Try to get progress from aria attribute or style
                    progress = (
                        progress_bar.get_attribute('aria-valuenow') or
                        progress_bar.get_attribute('value') or
                        self._extract_progress_from_style(progress_bar)
                    )
                    return int(progress) if progress else None
                except:
                    pass

        return None

    def _extract_progress_from_style(self, element) -> Optional[str]:
        """Extract progress value from element style."""
        style = element.get_attribute('style') or ''
        if 'width' in style:
            # Extract percentage from "width: 50%"
            import re
            match = re.search(r'width:\s*(\d+)%', style)
            if match:
                return match.group(1)
        return None

    def navigate_to_my_courses(self) -> None:
        """Navigate to My Courses section."""
        self.click_element(*self.NAV_MY_COURSES)
        self.waits.wait_for_loading_complete()

    def navigate_to_progress(self) -> None:
        """Navigate to Progress section."""
        self.click_element(*self.NAV_PROGRESS)
        self.waits.wait_for_loading_complete()

    def navigate_to_certificates(self) -> None:
        """Navigate to Certificates section."""
        self.click_element(*self.NAV_CERTIFICATES)
        self.waits.wait_for_loading_complete()

    def start_lab_for_course(self, course_title: str) -> bool:
        """
        Start lab environment for a course.

        Args:
            course_title: Title of course

        Returns:
            True if lab was started
        """
        if self.click_course(course_title):
            try:
                lab_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(self.LAB_BUTTON)
                )
                lab_button.click()
                self.waits.wait_for_loading_complete()
                return True
            except TimeoutException:
                logger.warning("Lab button not found")

        return False

    def take_quiz_for_course(self, course_title: str) -> bool:
        """
        Navigate to quiz for a course.

        Args:
            course_title: Title of course

        Returns:
            True if quiz page opened
        """
        if self.click_course(course_title):
            try:
                quiz_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(self.QUIZ_BUTTON)
                )
                quiz_button.click()
                self.waits.wait_for_loading_complete()
                return True
            except TimeoutException:
                logger.warning("Quiz button not found")

        return False

    def has_empty_state(self) -> bool:
        """Check if dashboard shows empty state (no enrolled courses)."""
        empty_state_selectors = [
            (By.CSS_SELECTOR, ".empty-state"),
            (By.CSS_SELECTOR, "[data-testid='no-courses']"),
            (By.XPATH, "//*[contains(text(), 'No courses')]"),
            (By.XPATH, "//*[contains(text(), 'not enrolled')]"),
        ]

        for selector in empty_state_selectors:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed():
                    return True
            except:
                pass

        return False
