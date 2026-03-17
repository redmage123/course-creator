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

    NOTE: CSS Modules are used in the frontend, so class names are hashed.
    We use robust selectors based on semantic structure rather than class names.
    """

    # List view locators - using semantic structure instead of hashed class names
    # Programs are displayed in cards with links to /courses/{id}
    PROGRAM_LIST = (By.CSS_SELECTOR, "main, [role='main'], .list-page")
    # Cards are divs containing links that start with /courses/
    PROGRAM_CARDS = (By.XPATH, "//a[starts-with(@href, '/courses/')]/ancestor::div[contains(@class, 'card') or contains(@class, 'Card') or position()=1]")
    # Alternative: Find all links to courses (these are inside program cards)
    PROGRAM_LINKS = (By.CSS_SELECTOR, "a[href^='/courses/']")
    PROGRAM_TITLE = (By.CSS_SELECTOR, "a[href^='/courses/'], h3, h4")
    PROGRAM_STATUS_BADGE = (By.XPATH, "//*[contains(text(), 'Published') or contains(text(), 'Draft')]")
    CREATE_BUTTON = (By.XPATH, "//button[contains(text(), 'Create') or contains(text(), 'New Program')]")
    FILTER_DROPDOWN = (By.CSS_SELECTOR, "select, [data-testid='filter'], .filter-dropdown")

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
        self._dismiss_modals()

    def _dismiss_modals(self) -> None:
        """Dismiss any modals (like AI welcome modal) that might be blocking."""
        import time

        modal_close_selectors = [
            (By.XPATH, "//button[text()='×']"),
            (By.XPATH, "//button[normalize-space()='×']"),
            (By.XPATH, "//button[contains(., 'Maybe Later')]"),
            (By.XPATH, "//button[contains(., 'Close')]"),
            (By.XPATH, "//button[contains(., \"Don't show\")]"),
            (By.CSS_SELECTOR, ".modal-close"),
            (By.CSS_SELECTOR, "[aria-label='Close']"),
            (By.CSS_SELECTOR, "[aria-label='close']"),
        ]

        for selector in modal_close_selectors:
            try:
                buttons = self.driver.find_elements(*selector)
                for btn in buttons:
                    if btn.is_displayed():
                        logger.debug(f"Dismissing modal with button: {btn.text}")
                        btn.click()
                        time.sleep(0.3)
            except:
                pass

    # ========================================================================
    # LIST VIEW METHODS
    # ========================================================================

    def navigate_to_list(self, role: str = "instructor") -> "TrainingProgramPage":
        """
        Navigate to the program list page using SPA navigation.

        CRITICAL: Uses JavaScript pushState navigation to preserve in-memory
        auth tokens. The frontend stores JWT tokens in memory (not localStorage)
        for security, so full page reloads (driver.get) lose authentication.

        Args:
            role: User role (instructor, org-admin)

        Returns:
            Self for method chaining
        """
        if role == "instructor":
            path = "/instructor/programs"
        elif role in ["org-admin", "organization_admin"]:
            path = "/organization/programs"
        else:
            path = "/programs"

        logger.info(f"SPA navigating to program list: {path}")

        # Use pushState + popstate event to trigger React Router navigation
        # without losing in-memory auth tokens
        self.driver.execute_script(f"""
            window.history.pushState({{}}, '', '{path}');
            window.dispatchEvent(new PopStateEvent('popstate', {{ state: {{}} }}));
        """)

        # Wait for React Router to process navigation
        import time
        time.sleep(0.5)

        self._wait_for_page_ready()
        return self

    def get_program_count(self) -> int:
        """
        Get count of programs in list.

        Returns:
            Number of visible program cards (based on links to /courses/)
        """
        self._wait_for_page_ready()
        # Use PROGRAM_LINKS selector which finds links to courses
        elements = self.find_elements(*self.PROGRAM_LINKS)
        visible_count = sum(1 for el in elements if el.is_displayed())
        logger.info(f"Found {visible_count} program links in UI")
        return visible_count

    def get_program_titles(self) -> List[str]:
        """
        Get titles of all programs in list.

        Returns:
            List of program titles (from links to /courses/)
        """
        self._wait_for_page_ready()
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

    def get_programs_with_status(self) -> List[dict]:
        """
        Get all programs with their status.

        Returns:
            List of dicts with 'title' and 'published' keys
        """
        self._wait_for_page_ready()
        # Find course links
        links = self.find_elements(*self.PROGRAM_LINKS)
        programs = []

        for link in links:
            if link.is_displayed():
                title = link.text.strip()
                if not title:
                    continue

                # Look for status badge in parent container
                try:
                    # Get parent card container (traverse up the DOM)
                    parent = link.find_element(By.XPATH, "./ancestor::div[1]")
                    card_text = parent.text.lower()
                    published = 'published' in card_text and 'draft' not in card_text
                except:
                    published = False

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
        links = self.find_elements(*self.PROGRAM_LINKS)

        for link in links:
            if title in link.text:
                self.scroll_to_element(link)
                link.click()
                self._wait_for_page_ready()
                return True

        logger.warning(f"Program not found: {title}")
        return False

    def click_create_program(self) -> bool:
        """
        Click Create Program button.

        The instructor programs page has these buttons:
        - "Create New Program" (in header when programs exist)
        - "Create First Program" (in empty state when no programs)

        NOTE: These buttons have nested <span> elements, so text() doesn't work.
        We must use normalize-space() or . (full text content) in XPath.

        Returns:
            True if button was clicked
        """
        create_selectors = [
            # Match using normalize-space (handles nested spans)
            (By.XPATH, "//button[normalize-space()='Create New Program']"),
            (By.XPATH, "//button[normalize-space()='Create First Program']"),
            # Match using . (full text content)
            (By.XPATH, "//button[.='Create New Program']"),
            (By.XPATH, "//button[.='Create First Program']"),
            # Partial matches
            (By.XPATH, "//button[contains(., 'Create New')]"),
            (By.XPATH, "//button[contains(., 'Create First')]"),
            (By.XPATH, "//button[contains(., 'Create Program')]"),
            # Generic matches
            (By.CSS_SELECTOR, "[data-testid='create-program']"),
            (By.XPATH, "//button[contains(., 'Create')]"),
            (By.XPATH, "//a[contains(., 'Create')]"),
            (By.CSS_SELECTOR, ".create-button"),
        ]

        for selector in create_selectors:
            try:
                button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(selector)
                )
                if button.is_displayed():
                    logger.info(f"Found create button with selector: {selector}")
                    button.click()
                    self._wait_for_page_ready()
                    return True
            except:
                continue

        logger.warning("Could not find create program button")
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

        The submit button on the create form is "Create Program" with nested span.

        Returns:
            True if form was submitted successfully
        """
        submit_selectors = [
            # Specific to create form - "Create Program" button
            (By.XPATH, "//button[normalize-space()='Create Program']"),
            (By.XPATH, "//button[.='Create Program']"),
            (By.XPATH, "//button[contains(., 'Create Program')]"),
            # Generic submit button
            (By.CSS_SELECTOR, "button[type='submit']"),
            # Other possible button texts (using . for nested spans)
            (By.XPATH, "//button[contains(., 'Save')]"),
            (By.XPATH, "//button[contains(., 'Submit')]"),
        ]

        for selector in submit_selectors:
            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(selector)
                )
                if button.is_displayed():
                    logger.info(f"Found submit button with selector: {selector}")
                    button.click()
                    self._wait_for_page_ready()
                    return True
            except:
                continue

        logger.warning("Could not find submit button")
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
