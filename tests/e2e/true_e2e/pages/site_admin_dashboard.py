"""
Site Admin Dashboard Page Object

Encapsulates interactions with the site admin dashboard for true E2E testing.
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


class SiteAdminDashboard(BasePage):
    """
    Page object for the site admin dashboard.

    Provides methods for:
    - Managing all organizations
    - Platform-wide user management
    - System configuration
    - Platform analytics
    """

    # Locators
    DASHBOARD_TITLE = (By.CSS_SELECTOR, "h1, .dashboard-title")

    # Organization management
    ORG_LIST = (By.CSS_SELECTOR, ".org-list, [data-testid='org-list']")
    ORG_ROW = (By.CSS_SELECTOR, ".org-row, [data-testid='org-row'], tr")
    ORG_NAME = (By.CSS_SELECTOR, ".org-name, td:first-child")
    CREATE_ORG_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-org'], .create-org")

    # User management
    USER_LIST = (By.CSS_SELECTOR, ".user-list, [data-testid='user-list']")
    USER_ROW = (By.CSS_SELECTOR, ".user-row, [data-testid='user-row'], tr")

    # Navigation
    NAV_DASHBOARD = (By.XPATH, "//a[contains(text(), 'Dashboard')]")
    NAV_ORGANIZATIONS = (By.XPATH, "//a[contains(text(), 'Organizations')]")
    NAV_USERS = (By.XPATH, "//a[contains(text(), 'Users')]")
    NAV_ANALYTICS = (By.XPATH, "//a[contains(text(), 'Analytics')]")
    NAV_SETTINGS = (By.XPATH, "//a[contains(text(), 'Settings')]")
    NAV_SYSTEM = (By.XPATH, "//a[contains(text(), 'System')]")

    # Statistics
    TOTAL_ORGS = (By.CSS_SELECTOR, "[data-testid='total-orgs'], .total-orgs")
    TOTAL_USERS = (By.CSS_SELECTOR, "[data-testid='total-users'], .total-users")
    ACTIVE_USERS = (By.CSS_SELECTOR, "[data-testid='active-users'], .active-users")

    # System status
    SYSTEM_STATUS = (By.CSS_SELECTOR, ".system-status, [data-testid='system-status']")
    SERVICE_STATUS = (By.CSS_SELECTOR, ".service-status, [data-testid='service-status']")

    def __init__(self, driver: WebDriver, config: SeleniumConfig):
        """Initialize site admin dashboard page object."""
        super().__init__(driver, config)
        self.waits = ReactWaitHelpers(driver)
        self.url = f"{self.base_url}/dashboard/admin"

    def navigate(self) -> "SiteAdminDashboard":
        """
        Navigate to the site admin dashboard.

        Returns:
            Self for method chaining
        """
        logger.info(f"Navigating to site admin dashboard: {self.url}")
        self.driver.get(self.url)
        self._wait_for_dashboard_ready()
        return self

    def _wait_for_dashboard_ready(self) -> None:
        """Wait for dashboard to be fully loaded."""
        self.waits.wait_for_loading_complete()
        self.waits.wait_for_react_query_idle()

    def is_on_dashboard(self) -> bool:
        """Check if currently on the site admin dashboard."""
        current_url = self.driver.current_url.lower()
        return 'admin' in current_url and 'dashboard' in current_url

    # ========================================================================
    # ORGANIZATION MANAGEMENT
    # ========================================================================

    def navigate_to_organizations(self) -> None:
        """Navigate to Organizations section."""
        self.click_element(*self.NAV_ORGANIZATIONS)
        self.waits.wait_for_loading_complete()

    def get_organization_count(self) -> int:
        """Get count of organizations."""
        try:
            stat = self.driver.find_element(*self.TOTAL_ORGS)
            import re
            match = re.search(r'(\d+)', stat.text)
            if match:
                return int(match.group(1))
        except:
            pass

        # Fall back to counting rows
        try:
            rows = self.find_elements(*self.ORG_ROW)
            return max(0, len([r for r in rows if r.is_displayed()]) - 1)
        except:
            return 0

    def get_organization_names(self) -> List[str]:
        """Get list of all organization names."""
        self.waits.wait_for_loading_complete()
        rows = self.find_elements(*self.ORG_ROW)
        names = []

        for row in rows:
            if row.is_displayed():
                try:
                    name_element = row.find_element(*self.ORG_NAME)
                    if name_element.text.strip():
                        names.append(name_element.text.strip())
                except:
                    pass

        return names

    def click_create_organization(self) -> bool:
        """Click Create Organization button."""
        try:
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(self.CREATE_ORG_BUTTON)
            )
            button.click()
            self.waits.wait_for_modal_open()
            return True
        except TimeoutException:
            return False

    def click_organization(self, org_name: str) -> bool:
        """Click on a specific organization."""
        rows = self.find_elements(*self.ORG_ROW)

        for row in rows:
            if org_name in row.text:
                row.click()
                self.waits.wait_for_loading_complete()
                return True

        return False

    # ========================================================================
    # USER MANAGEMENT
    # ========================================================================

    def navigate_to_users(self) -> None:
        """Navigate to Users section."""
        self.click_element(*self.NAV_USERS)
        self.waits.wait_for_loading_complete()

    def get_total_users(self) -> Optional[int]:
        """Get total user count."""
        try:
            stat = self.driver.find_element(*self.TOTAL_USERS)
            import re
            match = re.search(r'(\d+)', stat.text)
            if match:
                return int(match.group(1))
        except:
            pass
        return None

    def get_active_users(self) -> Optional[int]:
        """Get active user count."""
        try:
            stat = self.driver.find_element(*self.ACTIVE_USERS)
            import re
            match = re.search(r'(\d+)', stat.text)
            if match:
                return int(match.group(1))
        except:
            pass
        return None

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    def navigate_to_analytics(self) -> None:
        """Navigate to Analytics section."""
        self.click_element(*self.NAV_ANALYTICS)
        self.waits.wait_for_loading_complete()

    # ========================================================================
    # SYSTEM SETTINGS
    # ========================================================================

    def navigate_to_settings(self) -> None:
        """Navigate to Settings section."""
        self.click_element(*self.NAV_SETTINGS)
        self.waits.wait_for_loading_complete()

    def navigate_to_system(self) -> None:
        """Navigate to System section."""
        self.click_element(*self.NAV_SYSTEM)
        self.waits.wait_for_loading_complete()

    def get_system_status(self) -> Optional[str]:
        """Get overall system status."""
        try:
            element = self.driver.find_element(*self.SYSTEM_STATUS)
            return element.text
        except:
            return None

    def get_service_statuses(self) -> List[dict]:
        """Get status of all services."""
        statuses = []
        try:
            service_elements = self.find_elements(*self.SERVICE_STATUS)
            for element in service_elements:
                if element.is_displayed():
                    text = element.text
                    # Parse service status from text
                    statuses.append({
                        'text': text,
                        'healthy': 'healthy' in text.lower() or 'running' in text.lower()
                    })
        except:
            pass
        return statuses

    def has_admin_access(self) -> bool:
        """Verify admin-level access is available."""
        admin_indicators = [
            (By.XPATH, "//*[contains(text(), 'Site Admin')]"),
            (By.XPATH, "//*[contains(text(), 'Platform Admin')]"),
            (By.CSS_SELECTOR, "[data-testid='admin-panel']"),
            self.NAV_ORGANIZATIONS,
            self.NAV_SYSTEM,
        ]

        for selector in admin_indicators:
            try:
                element = self.driver.find_element(*selector)
                if element.is_displayed():
                    return True
            except:
                pass

        return False
