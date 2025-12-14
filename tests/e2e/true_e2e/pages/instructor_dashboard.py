"""
Instructor Dashboard Page Object

Encapsulates interactions with the instructor dashboard for true E2E testing.
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


class InstructorDashboard(BasePage):
    """
    Page object for the instructor dashboard.

    Provides methods for:
    - Viewing and managing training programs
    - Creating new programs
    - Managing students
    - Viewing analytics
    """

    # Locators - using semantic structure instead of hashed class names
    # NOTE: CSS Modules are used in the frontend, so class names are hashed.
    # We use robust selectors based on semantic structure (links, headings) rather than class names.
    DASHBOARD_TITLE = (By.CSS_SELECTOR, "h1, .dashboard-title, [data-testid='dashboard-title']")

    # Programs are displayed in cards with links to /courses/{id}
    PROGRAM_LINKS = (By.CSS_SELECTOR, "a[href^='/courses/']")
    PROGRAM_CARDS = (By.XPATH, "//a[starts-with(@href, '/courses/')]/ancestor::div[contains(@class, 'card') or contains(@class, 'Card') or position()=1]")
    PROGRAM_TITLE = (By.CSS_SELECTOR, "a[href^='/courses/'], h3, h4")
    CREATE_PROGRAM_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-program'], .create-program, button[class*='create']")
    STUDENT_COUNT = (By.CSS_SELECTOR, ".student-count, [data-testid='student-count']")

    # Navigation
    NAV_PROGRAMS = (By.XPATH, "//a[contains(text(), 'Programs') or contains(text(), 'Courses')]")
    NAV_STUDENTS = (By.XPATH, "//a[contains(text(), 'Students')]")
    NAV_ANALYTICS = (By.XPATH, "//a[contains(text(), 'Analytics')]")
    NAV_CONTENT = (By.XPATH, "//a[contains(text(), 'Content')]")

    # Program status indicators - check text content
    PROGRAM_STATUS = (By.XPATH, "//*[contains(text(), 'Published') or contains(text(), 'Draft')]")
    PUBLISHED_BADGE = (By.CSS_SELECTOR, ".published-badge, [data-status='published']")
    DRAFT_BADGE = (By.CSS_SELECTOR, ".draft-badge, [data-status='draft']")

    # Actions
    PUBLISH_BUTTON = (By.CSS_SELECTOR, "[data-testid='publish-program'], .publish-button")
    EDIT_BUTTON = (By.CSS_SELECTOR, "[data-testid='edit-program'], .edit-button")
    DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete-program'], .delete-button")

    def __init__(self, driver: WebDriver, config: SeleniumConfig):
        """Initialize instructor dashboard page object."""
        super().__init__(driver, config)
        self.waits = ReactWaitHelpers(driver)
        self.url = f"{self.base_url}/dashboard/instructor"

    def navigate(self) -> "InstructorDashboard":
        """
        Navigate to the instructor dashboard.

        Returns:
            Self for method chaining
        """
        logger.info(f"Navigating to instructor dashboard: {self.url}")
        self.driver.get(self.url)
        self._wait_for_dashboard_ready()
        return self

    def _wait_for_dashboard_ready(self) -> None:
        """Wait for dashboard to be fully loaded."""
        self.waits.wait_for_loading_complete()
        self.waits.wait_for_react_query_idle()

    def is_on_dashboard(self) -> bool:
        """Check if currently on the instructor dashboard."""
        current_url = self.driver.current_url.lower()
        return 'dashboard' in current_url and 'instructor' in current_url

    def get_program_count(self) -> int:
        """
        Get the number of programs displayed.

        Returns:
            Count of program links visible (based on links to /courses/)
        """
        self.waits.wait_for_loading_complete()
        self.waits.wait_for_react_query_idle()
        # Use PROGRAM_LINKS selector which finds links to courses
        elements = self.find_elements(*self.PROGRAM_LINKS)
        visible_count = sum(1 for el in elements if el.is_displayed())
        logger.info(f"Found {visible_count} program links in UI")
        return visible_count

    def get_program_titles(self) -> List[str]:
        """
        Get titles of all programs.

        Returns:
            List of program titles (from links to /courses/)
        """
        self.waits.wait_for_loading_complete()
        self.waits.wait_for_react_query_idle()
        # Use PROGRAM_LINKS to find course links - their text is the title
        links = self.find_elements(*self.PROGRAM_LINKS)
        titles = []

        for link in links:
            if link.is_displayed():
                title = link.text.strip()
                if title:
                    titles.append(title)

        logger.info(f"Found program titles: {titles}")
        return titles

    def click_create_program(self) -> bool:
        """
        Click the create program button.

        Returns:
            True if button was clicked successfully
        """
        create_selectors = [
            (By.CSS_SELECTOR, "[data-testid='create-program']"),
            (By.XPATH, "//button[contains(text(), 'Create')]"),
            (By.XPATH, "//button[contains(text(), 'New Program')]"),
            (By.XPATH, "//a[contains(text(), 'Create')]"),
            (By.CSS_SELECTOR, ".create-program"),
        ]

        for selector in create_selectors:
            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(selector)
                )
                if button.is_displayed():
                    button.click()
                    self.waits.wait_for_loading_complete()
                    return True
            except:
                continue

        logger.warning("Create program button not found")
        return False

    def click_program(self, program_title: str) -> bool:
        """
        Click on a specific program card.

        Args:
            program_title: Title of program to click

        Returns:
            True if program was found and clicked
        """
        links = self.find_elements(*self.PROGRAM_LINKS)

        for link in links:
            if program_title in link.text:
                self.scroll_to_element(link)
                link.click()
                self.waits.wait_for_loading_complete()
                return True

        logger.warning(f"Program not found: {program_title}")
        return False

    def is_program_published(self, program_title: str) -> Optional[bool]:
        """
        Check if a program is published.

        Args:
            program_title: Title of program

        Returns:
            True if published, False if draft, None if not found
        """
        links = self.find_elements(*self.PROGRAM_LINKS)

        for link in links:
            if program_title in link.text:
                # Get parent card container
                try:
                    parent = link.find_element(By.XPATH, "./ancestor::div[1]")
                    card_text = parent.text.lower()

                    # Check text content for status
                    if 'published' in card_text and 'draft' not in card_text:
                        return True
                    if 'draft' in card_text:
                        return False
                except:
                    pass

        return None

    def publish_program(self, program_title: str) -> bool:
        """
        Publish a program.

        Args:
            program_title: Title of program to publish

        Returns:
            True if program was published
        """
        if self.click_program(program_title):
            try:
                publish_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(self.PUBLISH_BUTTON)
                )
                publish_button.click()
                self.waits.wait_for_loading_complete()

                # Check for confirmation modal
                self.waits.wait_for_modal_close()
                return True
            except TimeoutException:
                logger.warning("Publish button not found")

        return False

    def navigate_to_programs(self) -> None:
        """Navigate to Programs/Courses section."""
        self.click_element(*self.NAV_PROGRAMS)
        self.waits.wait_for_loading_complete()

    def navigate_to_students(self) -> None:
        """Navigate to Students section."""
        self.click_element(*self.NAV_STUDENTS)
        self.waits.wait_for_loading_complete()

    def navigate_to_analytics(self) -> None:
        """Navigate to Analytics section."""
        self.click_element(*self.NAV_ANALYTICS)
        self.waits.wait_for_loading_complete()

    def get_student_count_for_program(self, program_title: str) -> Optional[int]:
        """
        Get number of enrolled students for a program.

        Args:
            program_title: Title of program

        Returns:
            Student count or None if not found
        """
        links = self.find_elements(*self.PROGRAM_LINKS)

        for link in links:
            if program_title in link.text:
                try:
                    # Get parent card container
                    parent = link.find_element(By.XPATH, "./ancestor::div[1]")
                    # Look for student count in parent text
                    card_text = parent.text
                    import re
                    # Match patterns like "5 students" or "5 enrolled"
                    match = re.search(r'(\d+)\s*(student|enrolled)', card_text.lower())
                    if match:
                        return int(match.group(1))
                except:
                    pass

        return None

    def has_empty_state(self) -> bool:
        """Check if dashboard shows empty state (no programs)."""
        empty_state_selectors = [
            (By.CSS_SELECTOR, ".empty-state"),
            (By.CSS_SELECTOR, "[data-testid='no-programs']"),
            (By.XPATH, "//*[contains(text(), 'No programs')]"),
            (By.XPATH, "//*[contains(text(), 'No courses')]"),
            (By.XPATH, "//*[contains(text(), 'Create your first')]"),
        ]

        for selector in empty_state_selectors:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed():
                    return True
            except:
                pass

        return False
