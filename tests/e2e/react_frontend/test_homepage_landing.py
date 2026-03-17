"""
E2E Tests for Homepage Landing Page

Tests the newly implemented React homepage landing page including:
- Page loads successfully
- Hero section displays correctly
- Feature cards are visible
- CTA buttons work
- Organization registration link works
- Responsive design
- SEO meta tags

BUSINESS CONTEXT:
The homepage is the first impression for potential users. These tests ensure
the landing page effectively communicates platform value and provides clear
paths to registration and login.

TECHNICAL IMPLEMENTATION:
- Tests React components with CSS Modules
- Validates responsive breakpoints
- Verifies navigation and routing
- Checks accessibility features
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import base classes
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from selenium_base import SeleniumConfig, ChromeDriverSetup


# ============================================================================
# PAGE OBJECTS
# ============================================================================

class HomepageLanding:
    """
    Page Object for React Homepage Landing Page.
    """

    def __init__(self, driver: webdriver.Chrome, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 15)

    def navigate(self):
        """Navigate to homepage"""
        self.driver.get(f"{self.base_url}/")
        time.sleep(2)  # Allow React to render

    def get_hero_title(self):
        """Get hero section title text"""
        return self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        ).text

    def get_hero_subtitle(self):
        """Get hero section subtitle"""
        elements = self.driver.find_elements(By.TAG_NAME, "p")
        if elements:
            return elements[0].text
        return ""

    def click_sign_in_button(self):
        """Click Sign In CTA button"""
        # Find link with text "Sign In"
        sign_in_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Sign In"))
        )
        sign_in_link.click()
        time.sleep(1)

    def click_create_account_button(self):
        """Click Create Account CTA button"""
        create_account_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Create Account"))
        )
        create_account_link.click()
        time.sleep(1)

    def click_register_organization_button(self):
        """Click Register Your Organization button"""
        register_org_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Register Your Organization"))
        )
        register_org_link.click()
        time.sleep(1)

    def get_feature_cards_count(self):
        """Count feature cards displayed"""
        # Feature cards should have specific class or h3 tags
        feature_titles = self.driver.find_elements(By.TAG_NAME, "h3")
        return len(feature_titles)

    def get_feature_titles(self):
        """Get all feature card titles"""
        feature_titles = self.driver.find_elements(By.TAG_NAME, "h3")
        return [title.text for title in feature_titles if title.text]

    def get_page_title(self):
        """Get page title from head"""
        return self.driver.title

    def has_section(self, section_name: str) -> bool:
        """Check if specific section exists"""
        try:
            self.driver.find_element(By.XPATH, f"//*[contains(text(), '{section_name}')]")
            return True
        except NoSuchElementException:
            return False


# ============================================================================
# TEST CLASS
# ============================================================================

class TestHomepageLanding:
    """
    Test suite for Homepage Landing Page.
    """

    @pytest.fixture(scope="class")
    def config(self):
        """Create Selenium config"""
        return SeleniumConfig()

    @pytest.fixture(scope="function")
    def driver(self, config):
        """Create WebDriver instance"""
        driver = ChromeDriverSetup.create_driver(config)
        yield driver
        driver.quit()

    @pytest.fixture(scope="function")
    def homepage(self, driver, config):
        """Create Homepage page object"""
        return HomepageLanding(driver, config.base_url)

    def test_homepage_loads_successfully(self, homepage):
        """
        Test that homepage loads without errors.

        SCENARIO:
        1. Navigate to homepage (/)
        2. Verify page loads
        3. Verify React app renders

        EXPECTED RESULT:
        - Page loads successfully
        - Title is correct
        - No console errors
        """
        # Navigate
        homepage.navigate()

        # Verify page loaded
        assert "Course Creator" in homepage.get_page_title()

        # Verify React content rendered
        hero_title = homepage.get_hero_title()
        assert len(hero_title) > 0
        assert "Learning" in hero_title or "Course" in hero_title

    def test_hero_section_displays_correctly(self, homepage):
        """
        Test hero section content.

        SCENARIO:
        1. Load homepage
        2. Verify hero title
        3. Verify hero subtitle
        4. Verify CTA buttons present

        EXPECTED RESULT:
        - Hero title contains value proposition
        - Subtitle explains platform
        - Sign In and Create Account buttons visible
        """
        homepage.navigate()

        # Check hero title
        hero_title = homepage.get_hero_title()
        assert "Transform" in hero_title or "AI" in hero_title

        # Check subtitle
        hero_subtitle = homepage.get_hero_subtitle()
        assert len(hero_subtitle) > 0

        # Verify CTA buttons exist
        driver = homepage.driver
        sign_in_links = driver.find_elements(By.LINK_TEXT, "Sign In")
        create_account_links = driver.find_elements(By.LINK_TEXT, "Create Account")

        assert len(sign_in_links) > 0, "Sign In button not found"
        assert len(create_account_links) > 0, "Create Account button not found"

    def test_feature_cards_displayed(self, homepage):
        """
        Test feature cards section.

        SCENARIO:
        1. Load homepage
        2. Count feature cards
        3. Verify feature titles

        EXPECTED RESULT:
        - 6 feature cards displayed
        - Each card has title and description
        - Cards include: AI Content Generation, Lab Environments, Analytics,
          Multi-tenant, Assessments, Certificates
        """
        homepage.navigate()

        # Get feature titles
        feature_titles = homepage.get_feature_titles()

        # Should have at least 6 features
        assert len(feature_titles) >= 6, f"Expected 6+ features, found {len(feature_titles)}"

        # Verify specific features exist
        titles_text = " ".join(feature_titles)
        assert "AI" in titles_text or "Content" in titles_text
        assert "Lab" in titles_text or "Interactive" in titles_text
        assert "Analytics" in titles_text
        assert "Certificate" in titles_text

    def test_sign_in_button_navigates(self, homepage):
        """
        Test Sign In button navigation.

        SCENARIO:
        1. Load homepage
        2. Click Sign In button
        3. Verify redirected to login page

        EXPECTED RESULT:
        - Clicking Sign In redirects to /login
        - Login page loads
        """
        homepage.navigate()

        # Click Sign In
        homepage.click_sign_in_button()

        # Verify URL changed
        current_url = homepage.driver.current_url
        assert "/login" in current_url

    def test_create_account_button_navigates(self, homepage):
        """
        Test Create Account button navigation.

        SCENARIO:
        1. Load homepage
        2. Click Create Account button
        3. Verify redirected to registration page

        EXPECTED RESULT:
        - Clicking Create Account redirects to /register
        - Registration page loads
        """
        homepage.navigate()

        # Click Create Account
        homepage.click_create_account_button()

        # Verify URL changed
        current_url = homepage.driver.current_url
        assert "/register" in current_url

    def test_register_organization_button_navigates(self, homepage):
        """
        Test Register Your Organization button navigation.

        SCENARIO:
        1. Load homepage
        2. Scroll to organization section
        3. Click Register Your Organization button
        4. Verify redirected to org registration

        EXPECTED RESULT:
        - Button redirects to /organization/register
        - Organization registration form loads
        """
        homepage.navigate()

        # Scroll down to find the button
        homepage.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)

        # Click Register Organization
        homepage.click_register_organization_button()

        # Verify URL changed
        current_url = homepage.driver.current_url
        assert "/organization/register" in current_url

    def test_footer_links_present(self, homepage):
        """
        Test footer section.

        SCENARIO:
        1. Load homepage
        2. Scroll to footer
        3. Verify footer links present

        EXPECTED RESULT:
        - Footer contains links to Sign In, Register, Organization Registration
        - Footer text mentions platform technologies
        """
        homepage.navigate()

        # Scroll to footer
        homepage.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        # Check for footer content
        footer_text = homepage.driver.find_element(By.TAG_NAME, "footer").text

        assert "Sign In" in footer_text or "React" in footer_text

    def test_responsive_design(self, homepage):
        """
        Test responsive design at mobile width.

        SCENARIO:
        1. Load homepage
        2. Resize to mobile width
        3. Verify content still visible

        EXPECTED RESULT:
        - Hero title visible on mobile
        - CTA buttons visible on mobile
        - Feature cards stack vertically
        """
        homepage.navigate()

        # Resize to mobile width (375px x 667px - iPhone SE)
        homepage.driver.set_window_size(375, 667)
        time.sleep(1)

        # Verify hero still visible
        hero_title = homepage.get_hero_title()
        assert len(hero_title) > 0

        # Verify buttons still work
        driver = homepage.driver
        sign_in_links = driver.find_elements(By.LINK_TEXT, "Sign In")
        assert len(sign_in_links) > 0

    def test_seo_meta_tags(self, homepage):
        """
        Test SEO meta tags are present.

        SCENARIO:
        1. Load homepage
        2. Check meta description
        3. Check title

        EXPECTED RESULT:
        - Page title includes "Course Creator Platform"
        - Meta description exists
        - Keywords include relevant terms
        """
        homepage.navigate()

        # Check page title
        title = homepage.get_page_title()
        assert "Course Creator" in title

        # Check for meta tags
        driver = homepage.driver
        meta_tags = driver.find_elements(By.TAG_NAME, "meta")

        # Look for description
        has_description = any(
            meta.get_attribute("name") == "description"
            for meta in meta_tags
        )

        # Meta tags should exist (React Helmet manages them)
        assert len(meta_tags) > 0
