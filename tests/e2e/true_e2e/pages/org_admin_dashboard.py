"""
Organization Admin Dashboard Page Object

Encapsulates interactions with the org admin dashboard for true E2E testing.
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


class OrgAdminDashboard(BasePage):
    """
    Page object for the organization admin dashboard.

    Provides methods for:
    - Managing organization members
    - Viewing all programs/courses
    - Managing tracks and projects
    - Organization settings

    NOTE: CSS Modules are used in the frontend, so class names are hashed.
    We use robust selectors based on semantic structure rather than class names.
    """

    # Locators - using semantic structure instead of hashed class names
    DASHBOARD_TITLE = (By.CSS_SELECTOR, "h1, .dashboard-title")
    ORG_NAME = (By.CSS_SELECTOR, "h1, h2, .org-name, [data-testid='org-name']")

    # Program/Course management - use links to /courses/
    PROGRAM_LINKS = (By.CSS_SELECTOR, "a[href^='/courses/']")
    PROGRAM_CARDS = (By.XPATH, "//a[starts-with(@href, '/courses/')]/ancestor::div[1]")
    PROGRAM_TITLE = (By.CSS_SELECTOR, "a[href^='/courses/'], h3, h4")
    PROGRAM_STATUS = (By.XPATH, "//*[contains(text(), 'Published') or contains(text(), 'Draft')]")

    # Member management
    MEMBER_LIST = (By.CSS_SELECTOR, ".member-list, [data-testid='member-list']")
    MEMBER_ROW = (By.CSS_SELECTOR, ".member-row, [data-testid='member-row'], tr")
    ADD_MEMBER_BUTTON = (By.CSS_SELECTOR, "[data-testid='add-member'], .add-member")

    # Navigation
    NAV_DASHBOARD = (By.XPATH, "//a[contains(text(), 'Dashboard')]")
    NAV_PROGRAMS = (By.XPATH, "//a[contains(text(), 'Programs') or contains(text(), 'Courses')]")
    NAV_MEMBERS = (By.XPATH, "//a[contains(text(), 'Members')]")
    NAV_TRACKS = (By.XPATH, "//a[contains(text(), 'Tracks')]")
    NAV_PROJECTS = (By.XPATH, "//a[contains(text(), 'Projects')]")
    NAV_SETTINGS = (By.XPATH, "//a[contains(text(), 'Settings')]")

    # Statistics
    TOTAL_MEMBERS = (By.CSS_SELECTOR, "[data-testid='total-members'], .total-members")
    TOTAL_PROGRAMS = (By.CSS_SELECTOR, "[data-testid='total-programs'], .total-programs")
    TOTAL_STUDENTS = (By.CSS_SELECTOR, "[data-testid='total-students'], .total-students")

    def __init__(self, driver: WebDriver, config: SeleniumConfig):
        """Initialize org admin dashboard page object."""
        super().__init__(driver, config)
        self.waits = ReactWaitHelpers(driver)
        self.url = f"{self.base_url}/dashboard/organization"

    def navigate(self) -> "OrgAdminDashboard":
        """
        Navigate to the org admin dashboard.

        Returns:
            Self for method chaining
        """
        logger.info(f"Navigating to org admin dashboard: {self.url}")
        self.driver.get(self.url)
        self._wait_for_dashboard_ready()
        return self

    def _wait_for_dashboard_ready(self) -> None:
        """Wait for dashboard to be fully loaded."""
        self.waits.wait_for_loading_complete()
        self.waits.wait_for_react_query_idle()

    def is_on_dashboard(self) -> bool:
        """Check if currently on the org admin dashboard."""
        current_url = self.driver.current_url.lower()
        return 'organization' in current_url or 'org-admin' in current_url

    def get_organization_name(self) -> Optional[str]:
        """Get the organization name displayed."""
        try:
            element = self.find_element(*self.ORG_NAME)
            return element.text
        except TimeoutException:
            return None

    # ========================================================================
    # PROGRAM/COURSE MANAGEMENT
    # ========================================================================

    def get_program_count(self) -> int:
        """
        Get the number of programs displayed.

        This should include BOTH published and unpublished programs.
        """
        self.waits.wait_for_loading_complete()
        self.waits.wait_for_react_query_idle()
        elements = self.find_elements(*self.PROGRAM_CARDS)
        return sum(1 for el in elements if el.is_displayed())

    def get_program_titles(self) -> List[str]:
        """
        Get titles of all programs.

        Should include both published and unpublished programs.
        """
        self.waits.wait_for_loading_complete()
        program_cards = self.find_elements(*self.PROGRAM_CARDS)
        titles = []

        for card in program_cards:
            if card.is_displayed():
                try:
                    title_element = card.find_element(*self.PROGRAM_TITLE)
                    titles.append(title_element.text)
                except:
                    text = card.text.split('\n')[0]
                    if text:
                        titles.append(text)

        return titles

    def get_programs_with_status(self) -> List[dict]:
        """
        Get all programs with their publication status.

        Returns:
            List of dicts with 'title' and 'published' keys
        """
        self.waits.wait_for_loading_complete()
        program_cards = self.find_elements(*self.PROGRAM_CARDS)
        programs = []

        for card in program_cards:
            if card.is_displayed():
                try:
                    title_element = card.find_element(*self.PROGRAM_TITLE)
                    title = title_element.text
                except:
                    title = card.text.split('\n')[0]

                # Determine status
                card_text = card.text.lower()
                published = 'published' in card_text or 'live' in card_text

                programs.append({
                    'title': title,
                    'published': published
                })

        return programs

    def navigate_to_programs(self) -> None:
        """Navigate to Programs/Courses section."""
        self.click_element(*self.NAV_PROGRAMS)
        self.waits.wait_for_loading_complete()
        self.waits.wait_for_react_query_idle()

    # ========================================================================
    # MEMBER MANAGEMENT
    # ========================================================================

    def navigate_to_members(self) -> None:
        """Navigate to Members section."""
        self.click_element(*self.NAV_MEMBERS)
        self.waits.wait_for_loading_complete()

    def get_member_count(self) -> int:
        """Get count of members displayed."""
        self.waits.wait_for_loading_complete()
        try:
            # First try specific stat element
            stat = self.driver.find_element(*self.TOTAL_MEMBERS)
            import re
            match = re.search(r'(\d+)', stat.text)
            if match:
                return int(match.group(1))
        except:
            pass

        # Fall back to counting rows
        try:
            rows = self.find_elements(*self.MEMBER_ROW)
            # Subtract 1 for header row if present
            return max(0, len([r for r in rows if r.is_displayed()]) - 1)
        except:
            return 0

    def click_add_member(self) -> bool:
        """Click Add Member button."""
        try:
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.ADD_MEMBER_BUTTON)
            )
            button.click()
            self.waits.wait_for_modal_open()
            return True
        except TimeoutException:
            return False

    # ========================================================================
    # TRACKS MANAGEMENT
    # ========================================================================

    def navigate_to_tracks(self) -> None:
        """Navigate to Tracks section."""
        self.click_element(*self.NAV_TRACKS)
        self.waits.wait_for_loading_complete()

    # ========================================================================
    # PROJECTS MANAGEMENT
    # ========================================================================

    def navigate_to_projects(self) -> None:
        """Navigate to Projects section."""
        self.click_element(*self.NAV_PROJECTS)
        self.waits.wait_for_loading_complete()

    # ========================================================================
    # SETTINGS
    # ========================================================================

    def navigate_to_settings(self) -> None:
        """Navigate to Settings section."""
        self.click_element(*self.NAV_SETTINGS)
        self.waits.wait_for_loading_complete()

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_total_students(self) -> Optional[int]:
        """Get total student count from stats."""
        try:
            element = self.driver.find_element(*self.TOTAL_STUDENTS)
            import re
            match = re.search(r'(\d+)', element.text)
            if match:
                return int(match.group(1))
        except:
            pass
        return None

    def get_total_programs_stat(self) -> Optional[int]:
        """Get total programs count from stats."""
        try:
            element = self.driver.find_element(*self.TOTAL_PROGRAMS)
            import re
            match = re.search(r'(\d+)', element.text)
            if match:
                return int(match.group(1))
        except:
            pass
        return None

    def has_empty_state(self) -> bool:
        """Check if dashboard shows empty state."""
        empty_selectors = [
            (By.CSS_SELECTOR, ".empty-state"),
            (By.XPATH, "//*[contains(text(), 'No programs')]"),
            (By.XPATH, "//*[contains(text(), 'No courses')]"),
            (By.XPATH, "//*[contains(text(), 'Get started')]"),
        ]

        for selector in empty_selectors:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed():
                    return True
            except:
                pass

        return False
