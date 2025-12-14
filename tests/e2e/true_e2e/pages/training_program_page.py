"""
Training Program Page Object

Encapsulates interactions with training program/course pages for true E2E testing.
Handles both list views and individual program details.
"""

import logging
from typing import List, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from tests.e2e.selenium_base import SeleniumConfig, BasePage
from tests.e2e.true_e2e.base.react_waits import ReactWaitHelpers

logger = logging.getLogger(__name__)


class TrainingProgramPage(BasePage):
    """
    Page object for training program pages.

    Handles:
    - Program list view
    - Program detail view
    - Program creation form
    - Program editing
    """

    # List view locators
    PROGRAM_LIST = (By.CSS_SELECTOR, ".program-list, [data-testid='program-list']")
    PROGRAM_CARDS = (By.CSS_SELECTOR, ".program-card, .course-card, [data-testid='program-card']")
    PROGRAM_TITLE = (By.CSS_SELECTOR, ".program-title, .course-title, .card-title, h3")
    PROGRAM_STATUS_BADGE = (By.CSS_SELECTOR, ".status-badge, [data-testid='status']")
    CREATE_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-program'], .create-button")
    FILTER_DROPDOWN = (By.CSS_SELECTOR, "[data-testid='filter'], .filter-dropdown")

    # Detail view locators
    DETAIL_TITLE = (By.CSS_SELECTOR, "h1, .program-title, [data-testid='program-title']")
    DETAIL_DESCRIPTION = (By.CSS_SELECTOR, ".description, [data-testid='description']")
    DETAIL_INSTRUCTOR = (By.CSS_SELECTOR, ".instructor, [data-testid='instructor']")
    DETAIL_DIFFICULTY = (By.CSS_SELECTOR, ".difficulty, [data-testid='difficulty']")
    EDIT_BUTTON = (By.CSS_SELECTOR, "[data-testid='edit-program'], .edit-button")
    PUBLISH_BUTTON = (By.CSS_SELECTOR, "[data-testid='publish'], .publish-button")
    UNPUBLISH_BUTTON = (By.CSS_SELECTOR, "[data-testid='unpublish'], .unpublish-button")
    DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete'], .delete-button")

    # Form locators
    FORM_TITLE = (By.NAME, "title")
    FORM_DESCRIPTION = (By.NAME, "description")
    FORM_DIFFICULTY = (By.NAME, "difficulty_level")
    FORM_DURATION = (By.NAME, "estimated_duration")
    FORM_DURATION_UNIT = (By.NAME, "duration_unit")
    FORM_SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")
    FORM_CANCEL = (By.CSS_SELECTOR, "[data-testid='cancel'], .cancel-button")

    # Alternative form locators
    FORM_TITLE_ALT = [
        (By.NAME, "title"),
        (By.ID, "title"),
        (By.CSS_SELECTOR, "input[placeholder*='title' i]"),
    ]

    FORM_DESCRIPTION_ALT = [
        (By.NAME, "description"),
        (By.ID, "description"),
        (By.CSS_SELECTOR, "textarea[placeholder*='description' i]"),
    ]

    def __init__(self, driver: WebDriver, config: SeleniumConfig):
        """Initialize training program page object."""
        super().__init__(driver, config)
        self.waits = ReactWaitHelpers(driver)

    def _wait_for_page_ready(self) -> None:
        """Wait for page to be fully loaded."""
        self.waits.wait_for_loading_complete()
        self.waits.wait_for_react_query_idle()

    # ========================================================================
    # LIST VIEW METHODS
    # ========================================================================

    def navigate_to_list(self, role: str = "instructor") -> "TrainingProgramPage":
        """
        Navigate to the program list page.

        Args:
            role: User role (instructor, org-admin)

        Returns:
            Self for method chaining
        """
        if role == "instructor":
            url = f"{self.base_url}/instructor/programs"
        elif role in ["org-admin", "organization_admin"]:
            url = f"{self.base_url}/organization/programs"
        else:
            url = f"{self.base_url}/programs"

        logger.info(f"Navigating to program list: {url}")
        self.driver.get(url)
        self._wait_for_page_ready()
        return self

    def get_program_count(self) -> int:
        """
        Get count of programs in list.

        Returns:
            Number of visible program cards
        """
        self._wait_for_page_ready()
        elements = self.find_elements(*self.PROGRAM_CARDS)
        return sum(1 for el in elements if el.is_displayed())

    def get_program_titles(self) -> List[str]:
        """
        Get titles of all programs in list.

        Returns:
            List of program titles
        """
        self._wait_for_page_ready()
        cards = self.find_elements(*self.PROGRAM_CARDS)
        titles = []

        for card in cards:
            if card.is_displayed():
                try:
                    title_el = card.find_element(*self.PROGRAM_TITLE)
                    titles.append(title_el.text)
                except:
                    text = card.text.split('\n')[0]
                    if text:
                        titles.append(text)

        return titles

    def get_programs_with_status(self) -> List[dict]:
        """
        Get all programs with their status.

        Returns:
            List of dicts with 'title' and 'published' keys
        """
        self._wait_for_page_ready()
        cards = self.find_elements(*self.PROGRAM_CARDS)
        programs = []

        for card in cards:
            if card.is_displayed():
                try:
                    title_el = card.find_element(*self.PROGRAM_TITLE)
                    title = title_el.text
                except:
                    title = card.text.split('\n')[0]

                card_text = card.text.lower()
                published = 'published' in card_text or 'live' in card_text

                programs.append({
                    'title': title,
                    'published': published
                })

        return programs

    def program_exists_in_list(self, title: str) -> bool:
        """
        Check if a program with given title exists in the list.

        Args:
            title: Program title to search for

        Returns:
            True if program found in list
        """
        titles = self.get_program_titles()
        return any(title in t for t in titles)

    def click_program(self, title: str) -> bool:
        """
        Click on a specific program.

        Args:
            title: Program title to click

        Returns:
            True if program was found and clicked
        """
        cards = self.find_elements(*self.PROGRAM_CARDS)

        for card in cards:
            if title in card.text:
                self.scroll_to_element(card)
                card.click()
                self._wait_for_page_ready()
                return True

        logger.warning(f"Program not found: {title}")
        return False

    def click_create_program(self) -> bool:
        """
        Click Create Program button.

        Returns:
            True if button was clicked
        """
        create_selectors = [
            (By.CSS_SELECTOR, "[data-testid='create-program']"),
            (By.XPATH, "//button[contains(text(), 'Create')]"),
            (By.XPATH, "//button[contains(text(), 'New')]"),
            (By.XPATH, "//a[contains(text(), 'Create')]"),
            (By.CSS_SELECTOR, ".create-button"),
        ]

        for selector in create_selectors:
            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(selector)
                )
                if button.is_displayed():
                    button.click()
                    self._wait_for_page_ready()
                    return True
            except:
                continue

        return False

    def has_empty_state(self) -> bool:
        """Check if list shows empty state."""
        empty_selectors = [
            (By.CSS_SELECTOR, ".empty-state"),
            (By.XPATH, "//*[contains(text(), 'No programs')]"),
            (By.XPATH, "//*[contains(text(), 'No courses')]"),
            (By.XPATH, "//*[contains(text(), 'Create your first')]"),
        ]

        for selector in empty_selectors:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed():
                    return True
            except:
                pass

        return False

    # ========================================================================
    # FORM METHODS
    # ========================================================================

    def fill_program_form(
        self,
        title: str,
        description: str = None,
        difficulty: str = "beginner",
        duration: int = None,
        duration_unit: str = None
    ) -> "TrainingProgramPage":
        """
        Fill out the program creation/edit form.

        Args:
            title: Program title
            description: Program description
            difficulty: Difficulty level
            duration: Estimated duration
            duration_unit: Duration unit (hours, days, weeks)

        Returns:
            Self for method chaining
        """
        # Fill title
        for selector in self.FORM_TITLE_ALT:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed():
                    element.clear()
                    element.send_keys(title)
                    break
            except:
                continue

        # Fill description
        if description:
            for selector in self.FORM_DESCRIPTION_ALT:
                try:
                    element = self.driver.find_element(*selector)
                    if element.is_displayed():
                        element.clear()
                        element.send_keys(description)
                        break
                except:
                    continue

        # Select difficulty
        try:
            difficulty_element = self.driver.find_element(*self.FORM_DIFFICULTY)
            if difficulty_element.tag_name.lower() == 'select':
                select = Select(difficulty_element)
                select.select_by_value(difficulty)
            else:
                # Maybe it's a custom dropdown
                difficulty_element.click()
                option = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//*[contains(text(), '{difficulty}')]")
                    )
                )
                option.click()
        except:
            pass

        # Fill duration if provided
        if duration:
            try:
                duration_element = self.driver.find_element(*self.FORM_DURATION)
                duration_element.clear()
                duration_element.send_keys(str(duration))
            except:
                pass

        if duration_unit:
            try:
                unit_element = self.driver.find_element(*self.FORM_DURATION_UNIT)
                if unit_element.tag_name.lower() == 'select':
                    select = Select(unit_element)
                    select.select_by_value(duration_unit)
            except:
                pass

        return self

    def submit_form(self) -> bool:
        """
        Submit the program form.

        Returns:
            True if form was submitted successfully
        """
        submit_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Save')]"),
            (By.XPATH, "//button[contains(text(), 'Create')]"),
            (By.XPATH, "//button[contains(text(), 'Submit')]"),
        ]

        for selector in submit_selectors:
            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(selector)
                )
                if button.is_displayed():
                    button.click()
                    self._wait_for_page_ready()
                    return True
            except:
                continue

        return False

    def cancel_form(self) -> None:
        """Cancel the form and return to list."""
        try:
            self.click_element(*self.FORM_CANCEL)
        except:
            # Navigate back
            self.driver.back()
        self._wait_for_page_ready()

    def get_form_error(self) -> Optional[str]:
        """Get any form validation error message."""
        error_selectors = [
            (By.CSS_SELECTOR, ".form-error"),
            (By.CSS_SELECTOR, ".error-message"),
            (By.CSS_SELECTOR, "[role='alert']"),
            (By.CSS_SELECTOR, ".validation-error"),
        ]

        for selector in error_selectors:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed() and element.text.strip():
                    return element.text.strip()
            except:
                pass

        return None

    # ========================================================================
    # DETAIL VIEW METHODS
    # ========================================================================

    def get_detail_title(self) -> Optional[str]:
        """Get program title from detail view."""
        try:
            element = self.find_element(*self.DETAIL_TITLE)
            return element.text
        except TimeoutException:
            return None

    def get_detail_description(self) -> Optional[str]:
        """Get program description from detail view."""
        try:
            element = self.find_element(*self.DETAIL_DESCRIPTION)
            return element.text
        except TimeoutException:
            return None

    def click_edit(self) -> bool:
        """Click Edit button on detail page."""
        try:
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.EDIT_BUTTON)
            )
            button.click()
            self._wait_for_page_ready()
            return True
        except TimeoutException:
            return False

    def click_publish(self) -> bool:
        """Click Publish button on detail page."""
        try:
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.PUBLISH_BUTTON)
            )
            button.click()
            self._wait_for_page_ready()
            self.waits.wait_for_modal_close()
            return True
        except TimeoutException:
            return False

    def click_unpublish(self) -> bool:
        """Click Unpublish button on detail page."""
        try:
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.UNPUBLISH_BUTTON)
            )
            button.click()
            self._wait_for_page_ready()
            self.waits.wait_for_modal_close()
            return True
        except TimeoutException:
            return False

    def is_published(self) -> bool:
        """Check if current program is published."""
        try:
            # Look for status badge
            badge = self.driver.find_element(*self.PROGRAM_STATUS_BADGE)
            return 'published' in badge.text.lower()
        except:
            pass

        # Check for publish/unpublish button presence
        try:
            self.driver.find_element(*self.UNPUBLISH_BUTTON)
            return True  # Unpublish button means it's published
        except:
            pass

        try:
            self.driver.find_element(*self.PUBLISH_BUTTON)
            return False  # Publish button means it's not published
        except:
            pass

        return False
