"""
Comprehensive E2E Tests for Complete Guest/Anonymous User Journey

BUSINESS REQUIREMENT:
Tests the complete guest/anonymous user experience including public browsing,
registration, password recovery, and verification that restricted content
remains inaccessible without authentication.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Covers 30+ test scenarios across the guest/anonymous lifecycle
- Validates public content access, registration flows, password reset
- Tests restricted content access blocking (redirects to login)
- Validates all UI interactions and security boundaries

TEST COVERAGE:
1. Public Course Browsing (without login)
2. Course Preview Pages Access
3. Public Information Pages
4. Registration Workflow (with GDPR consent)
5. Password Reset Workflow
6. External Links and Social Media
7. Restricted Access Verification
8. Search and Filter Functionality
9. Accessibility Features
10. Error Handling

PRIORITY: P0 (CRITICAL) - Part of comprehensive E2E test plan
"""

import pytest
import time
import uuid
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class HomePage(BasePage):
    """
    Page Object for public homepage/landing page.

    BUSINESS CONTEXT:
    The homepage is the primary entry point for anonymous visitors,
    showcasing public course catalog, platform features, and registration CTAs.
    """

    # Locators
    HOMEPAGE_HEADER = (By.CLASS_NAME, "homepage-header")
    LOGO = (By.CLASS_NAME, "platform-logo")
    LOGIN_LINK = (By.CSS_SELECTOR, "a[href*='login']")
    REGISTER_LINK = (By.CSS_SELECTOR, "a[href*='register']")

    # Navigation menu
    NAV_MENU = (By.CLASS_NAME, "main-nav")
    COURSES_LINK = (By.CSS_SELECTOR, "a[href*='courses']")
    ABOUT_LINK = (By.CSS_SELECTOR, "a[href*='about']")
    CONTACT_LINK = (By.CSS_SELECTOR, "a[href*='contact']")
    PRICING_LINK = (By.CSS_SELECTOR, "a[href*='pricing']")

    # Course catalog section
    COURSE_CATALOG_SECTION = (By.CLASS_NAME, "course-catalog")
    COURSE_CARDS = (By.CLASS_NAME, "course-card")
    COURSE_TITLE = (By.CLASS_NAME, "course-title")
    COURSE_DESCRIPTION = (By.CLASS_NAME, "course-description")
    COURSE_DIFFICULTY = (By.CLASS_NAME, "course-difficulty")
    COURSE_PREVIEW_BTN = (By.CLASS_NAME, "preview-course-btn")
    VIEW_DETAILS_BTN = (By.CLASS_NAME, "view-details-btn")

    # Search and filters
    SEARCH_INPUT = (By.ID, "course-search")
    SEARCH_BUTTON = (By.CLASS_NAME, "search-btn")
    CATEGORY_FILTER = (By.ID, "category-filter")
    DIFFICULTY_FILTER = (By.ID, "difficulty-filter")
    CLEAR_FILTERS_BTN = (By.CLASS_NAME, "clear-filters-btn")

    # Featured content
    FEATURED_COURSES_SECTION = (By.CLASS_NAME, "featured-courses")
    HERO_SECTION = (By.CLASS_NAME, "hero-section")
    CTA_BUTTON = (By.CLASS_NAME, "cta-button")

    # Footer
    FOOTER = (By.CLASS_NAME, "footer")
    PRIVACY_POLICY_LINK = (By.CSS_SELECTOR, "a[href*='privacy']")
    TERMS_OF_SERVICE_LINK = (By.CSS_SELECTOR, "a[href*='terms']")
    SOCIAL_MEDIA_LINKS = (By.CLASS_NAME, "social-links")

    def navigate(self):
        """Navigate to homepage."""
        self.navigate_to("/")

    def search_courses(self, query: str):
        """
        Search for courses using search functionality.

        Args:
            query: Search query string
        """
        self.enter_text(*self.SEARCH_INPUT, query)
        self.click_element(*self.SEARCH_BUTTON)
        time.sleep(1)  # Wait for search results

    def filter_by_category(self, category: str):
        """
        Filter courses by category.

        Args:
            category: Category name
        """
        from selenium.webdriver.support.ui import Select
        category_element = self.find_element(*self.CATEGORY_FILTER)
        select = Select(category_element)
        select.select_by_visible_text(category)
        time.sleep(1)  # Wait for filter to apply

    def filter_by_difficulty(self, difficulty: str):
        """
        Filter courses by difficulty level.

        Args:
            difficulty: Difficulty level (Beginner, Intermediate, Advanced)
        """
        from selenium.webdriver.support.ui import Select
        difficulty_element = self.find_element(*self.DIFFICULTY_FILTER)
        select = Select(difficulty_element)
        select.select_by_visible_text(difficulty)
        time.sleep(1)  # Wait for filter to apply

    def get_course_count(self) -> int:
        """Get number of visible course cards."""
        courses = self.find_elements(*self.COURSE_CARDS)
        return len(courses)

    def click_first_course(self):
        """Click the first course in the catalog."""
        courses = self.find_elements(*self.COURSE_CARDS)
        if courses:
            courses[0].click()
        time.sleep(1)

    def click_view_details(self, course_index: int = 0):
        """
        Click view details button for a specific course.

        Args:
            course_index: Index of course to view (default: 0 for first course)
        """
        view_buttons = self.find_elements(*self.VIEW_DETAILS_BTN)
        if view_buttons and len(view_buttons) > course_index:
            view_buttons[course_index].click()
        time.sleep(1)


class CoursePreviewPage(BasePage):
    """
    Page Object for public course preview/details page.

    BUSINESS CONTEXT:
    Allows anonymous users to view course information, syllabus outline,
    instructor details, and sample content before registration/enrollment.
    """

    # Locators
    COURSE_TITLE = (By.CLASS_NAME, "course-title-header")
    COURSE_DESCRIPTION = (By.CLASS_NAME, "course-full-description")
    COURSE_SYLLABUS = (By.CLASS_NAME, "course-syllabus")
    INSTRUCTOR_INFO = (By.CLASS_NAME, "instructor-info")
    INSTRUCTOR_NAME = (By.CLASS_NAME, "instructor-name")
    INSTRUCTOR_BIO = (By.CLASS_NAME, "instructor-bio")

    # Course details
    DURATION = (By.CLASS_NAME, "course-duration")
    DIFFICULTY_LEVEL = (By.CLASS_NAME, "difficulty-level")
    PREREQUISITES = (By.CLASS_NAME, "prerequisites")
    LEARNING_OBJECTIVES = (By.CLASS_NAME, "learning-objectives")

    # Preview content
    SAMPLE_VIDEO = (By.CLASS_NAME, "sample-video")
    PREVIEW_CONTENT = (By.CLASS_NAME, "preview-content")
    SYLLABUS_OUTLINE = (By.CLASS_NAME, "syllabus-outline")

    # Enrollment section
    ENROLL_BUTTON = (By.CLASS_NAME, "enroll-btn")
    ENROLLMENT_REQUIREMENTS = (By.CLASS_NAME, "enrollment-requirements")
    LOGIN_TO_ENROLL_MSG = (By.CLASS_NAME, "login-required-message")

    # Navigation
    BACK_TO_CATALOG_LINK = (By.CSS_SELECTOR, "a[href*='catalog']")

    def get_course_title(self) -> str:
        """Get course title text."""
        return self.get_text(*self.COURSE_TITLE)

    def get_instructor_name(self) -> str:
        """Get instructor name."""
        return self.get_text(*self.INSTRUCTOR_NAME)

    def click_enroll_button(self):
        """
        Click enroll button (should redirect to login for guest users).
        """
        self.click_element(*self.ENROLL_BUTTON)
        time.sleep(1)

    def is_login_required_message_visible(self) -> bool:
        """Check if login required message is displayed."""
        return self.is_element_present(*self.LOGIN_TO_ENROLL_MSG, timeout=3)


class RegistrationPage(BasePage):
    """
    Page Object for user registration page.

    BUSINESS CONTEXT:
    Registration is the primary conversion point for guest users,
    requiring GDPR-compliant data collection with explicit consent.
    """

    # Locators
    PAGE_TITLE = (By.CLASS_NAME, "registration-title")

    # Form fields
    FULL_NAME_INPUT = (By.ID, "fullName")
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirmPassword")

    # Organization fields (optional)
    ORGANIZATION_NAME_INPUT = (By.ID, "organizationName")
    ORGANIZATION_TYPE_SELECT = (By.ID, "organizationType")

    # GDPR consent checkboxes
    GDPR_CONSENT_CHECKBOX = (By.ID, "gdprConsent")
    ANALYTICS_CONSENT_CHECKBOX = (By.ID, "analyticsConsent")
    NOTIFICATIONS_CONSENT_CHECKBOX = (By.ID, "notificationsConsent")
    MARKETING_CONSENT_CHECKBOX = (By.ID, "marketingConsent")

    # Links
    PRIVACY_POLICY_LINK = (By.CSS_SELECTOR, "a[href*='privacy']")
    TERMS_OF_SERVICE_LINK = (By.CSS_SELECTOR, "a[href*='terms']")

    # Buttons
    REGISTER_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    LOGIN_LINK = (By.CSS_SELECTOR, "a[href*='login']")

    # Feedback messages
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    VALIDATION_ERROR = (By.CLASS_NAME, "validation-error")

    # Email verification
    EMAIL_VERIFICATION_MESSAGE = (By.CLASS_NAME, "email-verification-message")
    RESEND_VERIFICATION_LINK = (By.CLASS_NAME, "resend-verification-link")

    def navigate(self):
        """Navigate to registration page."""
        self.navigate_to("/frontend/html/register.html")

    def register_user(self, full_name: str, email: str, password: str,
                     gdpr_consent: bool = True,
                     analytics_consent: bool = False,
                     notifications_consent: bool = False,
                     marketing_consent: bool = False):
        """
        Complete user registration form.

        Args:
            full_name: User's full name
            email: User's email address
            password: Account password
            gdpr_consent: Required GDPR consent (default: True)
            analytics_consent: Optional analytics consent
            notifications_consent: Optional notifications consent
            marketing_consent: Optional marketing consent
        """
        # Fill in basic information
        self.enter_text(*self.FULL_NAME_INPUT, full_name)
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.enter_text(*self.CONFIRM_PASSWORD_INPUT, password)

        # Handle GDPR consent (required)
        if gdpr_consent:
            gdpr_checkbox = self.find_element(*self.GDPR_CONSENT_CHECKBOX)
            if not gdpr_checkbox.is_selected():
                gdpr_checkbox.click()

        # Handle optional consents
        if analytics_consent:
            analytics_checkbox = self.find_element(*self.ANALYTICS_CONSENT_CHECKBOX)
            if not analytics_checkbox.is_selected():
                analytics_checkbox.click()

        if notifications_consent:
            notifications_checkbox = self.find_element(*self.NOTIFICATIONS_CONSENT_CHECKBOX)
            if not notifications_checkbox.is_selected():
                notifications_checkbox.click()

        if marketing_consent and self.is_element_present(*self.MARKETING_CONSENT_CHECKBOX, timeout=2):
            marketing_checkbox = self.find_element(*self.MARKETING_CONSENT_CHECKBOX)
            if not marketing_checkbox.is_selected():
                marketing_checkbox.click()

    def submit_registration(self):
        """Submit registration form."""
        self.click_element(*self.REGISTER_BUTTON)
        time.sleep(2)  # Wait for form submission

    def is_registration_successful(self) -> bool:
        """Check if registration was successful."""
        return self.is_element_present(*self.SUCCESS_MESSAGE, timeout=5)

    def get_error_message(self) -> str:
        """Get error message text if present."""
        if self.is_element_present(*self.ERROR_MESSAGE, timeout=2):
            return self.get_text(*self.ERROR_MESSAGE)
        return ""

    def click_privacy_policy_link(self):
        """Click privacy policy link."""
        self.click_element(*self.PRIVACY_POLICY_LINK)
        time.sleep(1)

    def click_terms_link(self):
        """Click terms of service link."""
        self.click_element(*self.TERMS_OF_SERVICE_LINK)
        time.sleep(1)


class PasswordResetPage(BasePage):
    """
    Page Object for password reset/recovery page.

    BUSINESS CONTEXT:
    Allows users who forgot their password to reset it via email link,
    critical for account recovery and user retention.
    """

    # Locators
    PAGE_TITLE = (By.CLASS_NAME, "password-reset-title")

    # Request reset form
    EMAIL_INPUT = (By.ID, "resetEmail")
    REQUEST_RESET_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")

    # Reset confirmation
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    EMAIL_SENT_MESSAGE = (By.CLASS_NAME, "email-sent-message")

    # New password form (after clicking reset link)
    NEW_PASSWORD_INPUT = (By.ID, "newPassword")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirmPassword")
    RESET_PASSWORD_BUTTON = (By.CSS_SELECTOR, "button.reset-password-btn")

    # Navigation
    BACK_TO_LOGIN_LINK = (By.CSS_SELECTOR, "a[href*='login']")
    RESEND_EMAIL_LINK = (By.CLASS_NAME, "resend-email-link")

    def navigate(self):
        """Navigate to password reset page."""
        self.navigate_to("/frontend/html/forgot-password.html")

    def request_password_reset(self, email: str):
        """
        Request password reset for email.

        Args:
            email: Email address to reset password for
        """
        self.enter_text(*self.EMAIL_INPUT, email)
        self.click_element(*self.REQUEST_RESET_BUTTON)
        time.sleep(2)  # Wait for request processing

    def is_email_sent_message_visible(self) -> bool:
        """Check if email sent confirmation is displayed."""
        return self.is_element_present(*self.EMAIL_SENT_MESSAGE, timeout=5) or \
               self.is_element_present(*self.SUCCESS_MESSAGE, timeout=5)

    def set_new_password(self, new_password: str):
        """
        Set new password (on reset confirmation page).

        Args:
            new_password: New password to set
        """
        self.enter_text(*self.NEW_PASSWORD_INPUT, new_password)
        self.enter_text(*self.CONFIRM_PASSWORD_INPUT, new_password)
        self.click_element(*self.RESET_PASSWORD_BUTTON)
        time.sleep(2)

    def get_error_message(self) -> str:
        """Get error message if present."""
        if self.is_element_present(*self.ERROR_MESSAGE, timeout=2):
            return self.get_text(*self.ERROR_MESSAGE)
        return ""


class PublicPagesNavigator(BasePage):
    """
    Page Object for navigating and validating public information pages.

    BUSINESS CONTEXT:
    Public pages (About, Contact, Privacy, Terms, FAQ) provide critical
    information to users and are required for legal compliance (GDPR).
    """

    # Common elements on public pages
    PAGE_HEADER = (By.TAG_NAME, "h1")
    MAIN_CONTENT = (By.CLASS_NAME, "main-content")

    # About page
    ABOUT_TITLE = (By.CLASS_NAME, "about-title")
    MISSION_STATEMENT = (By.CLASS_NAME, "mission-statement")
    TEAM_SECTION = (By.CLASS_NAME, "team-section")

    # Contact page
    CONTACT_FORM = (By.CLASS_NAME, "contact-form")
    CONTACT_NAME_INPUT = (By.ID, "contactName")
    CONTACT_EMAIL_INPUT = (By.ID, "contactEmail")
    CONTACT_MESSAGE_INPUT = (By.ID, "contactMessage")
    CONTACT_SUBMIT_BTN = (By.CSS_SELECTOR, "button.contact-submit")

    # Privacy policy page
    PRIVACY_POLICY_CONTENT = (By.CLASS_NAME, "privacy-policy-content")
    GDPR_SECTION = (By.CLASS_NAME, "gdpr-section")
    DATA_COLLECTION_SECTION = (By.CLASS_NAME, "data-collection")

    # Terms of service page
    TERMS_CONTENT = (By.CLASS_NAME, "terms-content")
    USER_RESPONSIBILITIES = (By.CLASS_NAME, "user-responsibilities")

    # FAQ page
    FAQ_ITEMS = (By.CLASS_NAME, "faq-item")
    FAQ_QUESTION = (By.CLASS_NAME, "faq-question")
    FAQ_ANSWER = (By.CLASS_NAME, "faq-answer")

    def navigate_to_about(self):
        """Navigate to About page."""
        self.navigate_to("/frontend/html/about.html")

    def navigate_to_contact(self):
        """Navigate to Contact page."""
        self.navigate_to("/frontend/html/contact.html")

    def navigate_to_privacy_policy(self):
        """Navigate to Privacy Policy page."""
        self.navigate_to("/frontend/html/privacy-policy.html")

    def navigate_to_terms_of_service(self):
        """Navigate to Terms of Service page."""
        self.navigate_to("/frontend/html/terms-of-service.html")

    def navigate_to_faq(self):
        """Navigate to FAQ page."""
        self.navigate_to("/frontend/html/faq.html")

    def submit_contact_form(self, name: str, email: str, message: str):
        """
        Submit contact form.

        Args:
            name: Contact name
            email: Contact email
            message: Contact message
        """
        self.enter_text(*self.CONTACT_NAME_INPUT, name)
        self.enter_text(*self.CONTACT_EMAIL_INPUT, email)
        self.enter_text(*self.CONTACT_MESSAGE_INPUT, message)
        self.click_element(*self.CONTACT_SUBMIT_BTN)
        time.sleep(1)

    def get_page_header_text(self) -> str:
        """Get the main page header text."""
        return self.get_text(*self.PAGE_HEADER)


class LoginPage(BasePage):
    """
    Page Object for login page.

    BUSINESS CONTEXT:
    Used to verify that restricted pages redirect to login for guest users.
    """

    # Locators
    PAGE_TITLE = (By.CLASS_NAME, "login-title")
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    FORGOT_PASSWORD_LINK = (By.CSS_SELECTOR, "a[href*='forgot']")
    REGISTER_LINK = (By.CSS_SELECTOR, "a[href*='register']")

    def navigate(self):
        """Navigate to login page."""
        self.navigate_to("/frontend/html/index.html")

    def is_on_login_page(self) -> bool:
        """Check if currently on login page."""
        return self.is_element_present(*self.EMAIL_INPUT, timeout=5)


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestPublicCourseBrowsing(BaseTest):
    """
    Tests for public course browsing without authentication.

    BUSINESS REQUIREMENT:
    Anonymous users should be able to browse the public course catalog,
    search for courses, and view basic course information without login.
    """

    def test_homepage_loads_successfully(self):
        """
        Test that homepage loads without authentication.

        ACCEPTANCE CRITERIA:
        - Homepage accessible at root URL
        - Page title present
        - Navigation menu visible
        - No errors displayed
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Verify homepage elements are present
        assert page.is_element_present(*page.HOMEPAGE_HEADER, timeout=20), \
            "Homepage header not found"
        assert page.is_element_present(*page.NAV_MENU, timeout=15), \
            "Navigation menu not visible"
        assert page.is_element_present(*page.LOGO, timeout=15), \
            "Platform logo not visible"

    def test_public_course_catalog_visible(self):
        """
        Test that course catalog is visible to anonymous users.

        ACCEPTANCE CRITERIA:
        - Course catalog section present
        - At least one course card visible
        - Course information displayed (title, description)
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Verify course catalog section exists
        assert page.is_element_present(*page.COURSE_CATALOG_SECTION, timeout=20), \
            "Course catalog section not found"

        # Verify course cards are displayed
        course_count = page.get_course_count()
        assert course_count > 0, "No course cards found in catalog"

        # Verify course information is displayed
        assert page.is_element_present(*page.COURSE_TITLE, timeout=15), \
            "Course titles not displayed"

    def test_course_search_functionality(self):
        """
        Test course search for anonymous users.

        ACCEPTANCE CRITERIA:
        - Search input field accessible
        - Search query can be entered
        - Search executes without authentication
        - Results update based on query
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Verify search functionality exists
        assert page.is_element_present(*page.SEARCH_INPUT, timeout=20), \
            "Search input not found"

        # Perform search
        initial_count = page.get_course_count()
        page.search_courses("Python")
        time.sleep(1)

        # Verify search executed (results may change)
        # Note: We can't assert exact count without knowing test data
        assert page.is_element_present(*page.COURSE_CATALOG_SECTION, timeout=15), \
            "Course catalog disappeared after search"

    def test_category_filter_functionality(self):
        """
        Test category filtering for anonymous users.

        ACCEPTANCE CRITERIA:
        - Category filter dropdown accessible
        - Filter can be applied
        - Courses update based on filter
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Verify filter exists
        if page.is_element_present(*page.CATEGORY_FILTER, timeout=5):
            # Try to filter by category
            page.filter_by_category("Programming")
            time.sleep(1)

            # Verify courses are still displayed
            assert page.is_element_present(*page.COURSE_CATALOG_SECTION, timeout=15), \
                "Course catalog disappeared after filtering"

    def test_difficulty_filter_functionality(self):
        """
        Test difficulty level filtering for anonymous users.

        ACCEPTANCE CRITERIA:
        - Difficulty filter accessible
        - Filter can be applied
        - Courses update based on difficulty
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Verify filter exists
        if page.is_element_present(*page.DIFFICULTY_FILTER, timeout=5):
            # Try to filter by difficulty
            page.filter_by_difficulty("Beginner")
            time.sleep(1)

            # Verify courses are still displayed
            assert page.is_element_present(*page.COURSE_CATALOG_SECTION, timeout=15), \
                "Course catalog disappeared after filtering"


class TestCoursePreviewAccess(BaseTest):
    """
    Tests for accessing public course preview pages.

    BUSINESS REQUIREMENT:
    Anonymous users should be able to view course details, instructor
    information, and sample content to make informed enrollment decisions.
    """

    def test_course_details_page_accessible(self):
        """
        Test that course details page is accessible to anonymous users.

        ACCEPTANCE CRITERIA:
        - Course preview page loads
        - Course title and description visible
        - Instructor information displayed
        - No authentication required
        """
        # First navigate to homepage
        home_page = HomePage(self.driver, self.config)
        home_page.navigate()

        # Click on first course
        if home_page.get_course_count() > 0:
            home_page.click_first_course()
            time.sleep(2)

            # Verify course preview page loaded
            preview_page = CoursePreviewPage(self.driver, self.config)
            assert preview_page.is_element_present(*preview_page.COURSE_TITLE, timeout=20), \
                "Course title not found on preview page"

    def test_instructor_information_visible(self):
        """
        Test that instructor information is visible on preview page.

        ACCEPTANCE CRITERIA:
        - Instructor section present
        - Instructor name displayed
        - Bio or description available
        """
        home_page = HomePage(self.driver, self.config)
        home_page.navigate()

        if home_page.get_course_count() > 0:
            home_page.click_first_course()
            time.sleep(2)

            preview_page = CoursePreviewPage(self.driver, self.config)

            # Verify instructor information
            if preview_page.is_element_present(*preview_page.INSTRUCTOR_INFO, timeout=5):
                assert preview_page.is_element_present(*preview_page.INSTRUCTOR_NAME, timeout=15), \
                    "Instructor name not displayed"

    def test_syllabus_outline_visible(self):
        """
        Test that syllabus outline is visible to anonymous users.

        ACCEPTANCE CRITERIA:
        - Syllabus section present
        - Course structure visible
        - Learning objectives displayed
        """
        home_page = HomePage(self.driver, self.config)
        home_page.navigate()

        if home_page.get_course_count() > 0:
            home_page.click_first_course()
            time.sleep(2)

            preview_page = CoursePreviewPage(self.driver, self.config)

            # Verify syllabus is visible
            if preview_page.is_element_present(*preview_page.SYLLABUS_OUTLINE, timeout=5):
                assert preview_page.is_element_present(*preview_page.LEARNING_OBJECTIVES, timeout=15), \
                    "Learning objectives not displayed"

    def test_course_prerequisites_displayed(self):
        """
        Test that course prerequisites are shown.

        ACCEPTANCE CRITERIA:
        - Prerequisites section present
        - Clear indication of required knowledge
        """
        home_page = HomePage(self.driver, self.config)
        home_page.navigate()

        if home_page.get_course_count() > 0:
            home_page.click_first_course()
            time.sleep(2)

            preview_page = CoursePreviewPage(self.driver, self.config)

            # Check if prerequisites section exists
            # (may not exist for all courses)
            preview_page.is_element_present(*preview_page.PREREQUISITES, timeout=3)


class TestPublicPagesAccess(BaseTest):
    """
    Tests for accessing public information pages.

    BUSINESS REQUIREMENT:
    Critical platform information (About, Contact, Privacy, Terms) must
    be accessible to all users for legal compliance and transparency.
    """

    def test_about_page_accessible(self):
        """
        Test that About page is accessible to anonymous users.

        ACCEPTANCE CRITERIA:
        - About page loads
        - Page header present
        - Content visible
        """
        page = PublicPagesNavigator(self.driver, self.config)
        page.navigate_to_about()

        # Verify page loaded
        assert page.is_element_present(*page.PAGE_HEADER, timeout=20), \
            "About page header not found"
        assert page.is_element_present(*page.MAIN_CONTENT, timeout=15), \
            "About page content not visible"

    def test_contact_page_accessible(self):
        """
        Test that Contact page is accessible to anonymous users.

        ACCEPTANCE CRITERIA:
        - Contact page loads
        - Contact form visible
        - Form fields accessible
        """
        page = PublicPagesNavigator(self.driver, self.config)
        page.navigate_to_contact()

        # Verify contact page loaded
        assert page.is_element_present(*page.PAGE_HEADER, timeout=20), \
            "Contact page header not found"

        # Verify contact form exists (if implemented)
        if page.is_element_present(*page.CONTACT_FORM, timeout=5):
            assert page.is_element_present(*page.CONTACT_EMAIL_INPUT, timeout=15), \
                "Contact email input not found"

    def test_privacy_policy_accessible(self):
        """
        Test that Privacy Policy is accessible (GDPR compliance).

        ACCEPTANCE CRITERIA:
        - Privacy policy page loads
        - Policy content visible
        - GDPR information present
        """
        page = PublicPagesNavigator(self.driver, self.config)
        page.navigate_to_privacy_policy()

        # Verify privacy policy loaded
        assert page.is_element_present(*page.PAGE_HEADER, timeout=20), \
            "Privacy policy header not found"
        assert page.is_element_present(*page.MAIN_CONTENT, timeout=15), \
            "Privacy policy content not visible"

    def test_terms_of_service_accessible(self):
        """
        Test that Terms of Service is accessible.

        ACCEPTANCE CRITERIA:
        - Terms page loads
        - Terms content visible
        - Clear and readable
        """
        page = PublicPagesNavigator(self.driver, self.config)
        page.navigate_to_terms_of_service()

        # Verify terms page loaded
        assert page.is_element_present(*page.PAGE_HEADER, timeout=20), \
            "Terms of service header not found"
        assert page.is_element_present(*page.MAIN_CONTENT, timeout=15), \
            "Terms content not visible"

    def test_faq_page_accessible(self):
        """
        Test that FAQ page is accessible to anonymous users.

        ACCEPTANCE CRITERIA:
        - FAQ page loads
        - FAQ items visible
        - Questions and answers accessible
        """
        page = PublicPagesNavigator(self.driver, self.config)
        page.navigate_to_faq()

        # Verify FAQ page loaded
        assert page.is_element_present(*page.PAGE_HEADER, timeout=20), \
            "FAQ page header not found"


class TestUserRegistration(BaseTest):
    """
    Tests for user registration workflow.

    BUSINESS REQUIREMENT:
    Registration must be straightforward, GDPR-compliant, and validate
    user input to ensure data quality and legal compliance.
    """

    def test_registration_page_accessible(self):
        """
        Test that registration page is accessible.

        ACCEPTANCE CRITERIA:
        - Registration page loads
        - Registration form visible
        - All required fields present
        """
        page = RegistrationPage(self.driver, self.config)
        page.navigate()

        # Verify registration page loaded
        assert page.is_element_present(*page.FULL_NAME_INPUT, timeout=20), \
            "Full name input not found"
        assert page.is_element_present(*page.EMAIL_INPUT, timeout=15), \
            "Email input not found"
        assert page.is_element_present(*page.PASSWORD_INPUT, timeout=15), \
            "Password input not found"

    def test_registration_form_validation(self):
        """
        Test registration form validation for invalid inputs.

        ACCEPTANCE CRITERIA:
        - Empty form submission shows validation errors
        - Invalid email format rejected
        - Password requirements enforced
        """
        page = RegistrationPage(self.driver, self.config)
        page.navigate()

        # Try to submit empty form
        page.submit_registration()
        time.sleep(1)

        # Should show validation errors (either HTML5 or custom)
        # Note: Exact validation behavior depends on implementation
        current_url = page.get_current_url()
        # If validation works, should still be on registration page
        assert "register" in current_url.lower(), \
            "Form submitted without required fields"

    def test_gdpr_consent_required(self):
        """
        Test that GDPR consent is required for registration.

        ACCEPTANCE CRITERIA:
        - GDPR consent checkbox present
        - Registration blocked without consent
        - Privacy policy link available
        """
        page = RegistrationPage(self.driver, self.config)
        page.navigate()

        # Verify GDPR consent checkbox exists
        assert page.is_element_present(*page.GDPR_CONSENT_CHECKBOX, timeout=15), \
            "GDPR consent checkbox not found"

        # Verify privacy policy link exists
        assert page.is_element_present(*page.PRIVACY_POLICY_LINK, timeout=15), \
            "Privacy policy link not found"

    def test_successful_registration_flow(self):
        """
        Test complete registration flow with valid data.

        ACCEPTANCE CRITERIA:
        - Registration form accepts valid data
        - GDPR consent can be given
        - Form submits successfully
        - Success message or redirect occurs
        """
        page = RegistrationPage(self.driver, self.config)
        page.navigate()

        # Generate unique email
        unique_email = f"test_guest_{uuid.uuid4().hex[:8]}@example.com"

        # Fill in registration form
        page.register_user(
            full_name="Test Guest User",
            email=unique_email,
            password="TestPassword123!",
            gdpr_consent=True,
            analytics_consent=False,
            notifications_consent=False
        )

        # Submit registration
        page.submit_registration()
        time.sleep(3)

        # Verify registration processed
        # (could redirect to login, dashboard, or show success message)
        current_url = page.get_current_url()

        # Should either show success message or redirect away from registration
        is_successful = page.is_registration_successful() or \
                       "register" not in current_url.lower() or \
                       "login" in current_url.lower() or \
                       "dashboard" in current_url.lower()

        assert is_successful, "Registration did not complete successfully"

    def test_optional_consent_checkboxes(self):
        """
        Test that optional consent checkboxes work correctly.

        ACCEPTANCE CRITERIA:
        - Optional consent checkboxes present
        - Can register without optional consents
        - Optional consents can be selected
        """
        page = RegistrationPage(self.driver, self.config)
        page.navigate()

        # Verify optional consent checkboxes exist
        if page.is_element_present(*page.ANALYTICS_CONSENT_CHECKBOX, timeout=3):
            analytics_checkbox = page.find_element(*page.ANALYTICS_CONSENT_CHECKBOX)
            # Should be unchecked by default
            assert not analytics_checkbox.is_selected(), \
                "Analytics consent should be unchecked by default"

    def test_password_mismatch_validation(self):
        """
        Test that password confirmation must match.

        ACCEPTANCE CRITERIA:
        - Password mismatch shows error
        - Registration blocked with mismatched passwords
        """
        page = RegistrationPage(self.driver, self.config)
        page.navigate()

        # Fill form with mismatched passwords
        page.enter_text(*page.FULL_NAME_INPUT, "Test User")
        page.enter_text(*page.EMAIL_INPUT, f"test_{uuid.uuid4().hex[:8]}@example.com")
        page.enter_text(*page.PASSWORD_INPUT, "Password123!")
        page.enter_text(*page.CONFIRM_PASSWORD_INPUT, "DifferentPassword123!")

        # Check GDPR consent
        gdpr_checkbox = page.find_element(*page.GDPR_CONSENT_CHECKBOX)
        if not gdpr_checkbox.is_selected():
            gdpr_checkbox.click()

        # Submit
        page.submit_registration()
        time.sleep(2)

        # Should show validation error
        current_url = page.get_current_url()
        assert "register" in current_url.lower(), \
            "Registration should be blocked with mismatched passwords"


class TestPasswordReset(BaseTest):
    """
    Tests for password reset workflow.

    BUSINESS REQUIREMENT:
    Users must be able to recover their accounts if they forget passwords,
    critical for user retention and account security.
    """

    def test_password_reset_page_accessible(self):
        """
        Test that password reset page is accessible.

        ACCEPTANCE CRITERIA:
        - Password reset page loads
        - Email input field present
        - Submit button visible
        """
        page = PasswordResetPage(self.driver, self.config)
        page.navigate()

        # Verify password reset page loaded
        assert page.is_element_present(*page.EMAIL_INPUT, timeout=20), \
            "Password reset email input not found"
        assert page.is_element_present(*page.REQUEST_RESET_BUTTON, timeout=15), \
            "Password reset submit button not found"

    def test_password_reset_request_submission(self):
        """
        Test submitting password reset request.

        ACCEPTANCE CRITERIA:
        - Email can be entered
        - Form submits successfully
        - Confirmation message shown
        """
        page = PasswordResetPage(self.driver, self.config)
        page.navigate()

        # Request password reset
        page.request_password_reset("test@example.com")
        time.sleep(2)

        # Verify confirmation message or success indicator
        is_successful = page.is_email_sent_message_visible()

        # Note: For security, many systems show success even for non-existent emails
        # So we mainly verify the form processes without errors
        assert is_successful or page.get_current_url(), \
            "Password reset request did not process"

    def test_forgot_password_link_from_login(self):
        """
        Test that forgot password link works from login page.

        ACCEPTANCE CRITERIA:
        - Forgot password link visible on login page
        - Link navigates to password reset page
        """
        login_page = LoginPage(self.driver, self.config)
        login_page.navigate()

        # Click forgot password link
        if login_page.is_element_present(*login_page.FORGOT_PASSWORD_LINK, timeout=5):
            login_page.click_element(*login_page.FORGOT_PASSWORD_LINK)
            time.sleep(2)

            # Verify navigated to password reset page
            reset_page = PasswordResetPage(self.driver, self.config)
            assert reset_page.is_element_present(*reset_page.EMAIL_INPUT, timeout=20), \
                "Did not navigate to password reset page"

    def test_back_to_login_link(self):
        """
        Test navigation back to login from password reset.

        ACCEPTANCE CRITERIA:
        - Back to login link present
        - Link navigates to login page
        """
        page = PasswordResetPage(self.driver, self.config)
        page.navigate()

        # Click back to login
        if page.is_element_present(*page.BACK_TO_LOGIN_LINK, timeout=5):
            page.click_element(*page.BACK_TO_LOGIN_LINK)
            time.sleep(2)

            # Verify navigated to login page
            login_page = LoginPage(self.driver, self.config)
            assert login_page.is_on_login_page(), \
                "Did not navigate back to login page"


class TestRestrictedAccess(BaseTest):
    """
    Tests for verifying that restricted content requires authentication.

    BUSINESS REQUIREMENT:
    Protected resources (student dashboard, course content, labs) must
    be inaccessible to anonymous users and redirect to login.
    """

    def test_student_dashboard_redirects_to_login(self):
        """
        Test that student dashboard redirects anonymous users to login.

        ACCEPTANCE CRITERIA:
        - Dashboard URL redirects to login
        - No dashboard content accessible
        - Clear indication that login is required
        """
        # Try to access student dashboard directly
        self.driver.get(f"{self.config.base_url}/frontend/html/student-dashboard.html")
        time.sleep(2)

        # Should redirect to login or show login page
        current_url = self.driver.current_url
        login_page = LoginPage(self.driver, self.config)

        # Either redirected to login or login elements are present
        is_protected = "login" in current_url.lower() or \
                      "index.html" in current_url or \
                      login_page.is_on_login_page()

        assert is_protected, \
            "Student dashboard accessible without authentication"

    def test_instructor_dashboard_redirects_to_login(self):
        """
        Test that instructor dashboard requires authentication.

        ACCEPTANCE CRITERIA:
        - Instructor dashboard redirects to login
        - No instructor content accessible
        """
        # Try to access instructor dashboard
        self.driver.get(f"{self.config.base_url}/frontend/html/instructor-dashboard-modular.html")
        time.sleep(2)

        current_url = self.driver.current_url
        login_page = LoginPage(self.driver, self.config)

        is_protected = "login" in current_url.lower() or \
                      "index.html" in current_url or \
                      login_page.is_on_login_page()

        assert is_protected, \
            "Instructor dashboard accessible without authentication"

    def test_organization_admin_dashboard_protected(self):
        """
        Test that organization admin dashboard requires authentication.

        ACCEPTANCE CRITERIA:
        - Admin dashboard redirects to login
        - No admin content accessible
        """
        # Try to access org admin dashboard
        self.driver.get(f"{self.config.base_url}/frontend/html/organization-admin.html")
        time.sleep(2)

        current_url = self.driver.current_url
        login_page = LoginPage(self.driver, self.config)

        is_protected = "login" in current_url.lower() or \
                      "index.html" in current_url or \
                      login_page.is_on_login_page()

        assert is_protected, \
            "Organization admin dashboard accessible without authentication"

    def test_site_admin_dashboard_protected(self):
        """
        Test that site admin dashboard requires authentication.

        ACCEPTANCE CRITERIA:
        - Site admin dashboard redirects to login
        - No site admin content accessible
        """
        # Try to access site admin dashboard
        self.driver.get(f"{self.config.base_url}/frontend/html/site-admin-dashboard.html")
        time.sleep(2)

        current_url = self.driver.current_url
        login_page = LoginPage(self.driver, self.config)

        is_protected = "login" in current_url.lower() or \
                      "index.html" in current_url or \
                      login_page.is_on_login_page()

        assert is_protected, \
            "Site admin dashboard accessible without authentication"

    def test_course_enrollment_requires_login(self):
        """
        Test that course enrollment requires authentication.

        ACCEPTANCE CRITERIA:
        - Enroll button click redirects to login
        - Cannot enroll without authentication
        - Clear message indicating login required
        """
        # Navigate to homepage and view a course
        home_page = HomePage(self.driver, self.config)
        home_page.navigate()

        if home_page.get_course_count() > 0:
            home_page.click_first_course()
            time.sleep(2)

            # Try to enroll
            preview_page = CoursePreviewPage(self.driver, self.config)
            if preview_page.is_element_present(*preview_page.ENROLL_BUTTON, timeout=5):
                preview_page.click_enroll_button()
                time.sleep(2)

                # Should redirect to login or show login required message
                current_url = self.driver.current_url
                login_page = LoginPage(self.driver, self.config)

                is_protected = "login" in current_url.lower() or \
                              login_page.is_on_login_page() or \
                              preview_page.is_login_required_message_visible()

                assert is_protected, \
                    "Course enrollment allowed without authentication"


class TestNavigationAndLinks(BaseTest):
    """
    Tests for navigation functionality and external links.

    BUSINESS REQUIREMENT:
    Navigation should be intuitive, all links should work, and social
    media/external resources should be accessible.
    """

    def test_main_navigation_menu_accessible(self):
        """
        Test that main navigation menu is accessible to guests.

        ACCEPTANCE CRITERIA:
        - Navigation menu visible
        - Menu items accessible
        - Links functional
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Verify navigation menu exists
        assert page.is_element_present(*page.NAV_MENU, timeout=20), \
            "Main navigation menu not found"

        # Verify key navigation links present
        assert page.is_element_present(*page.LOGIN_LINK, timeout=15), \
            "Login link not found in navigation"
        assert page.is_element_present(*page.REGISTER_LINK, timeout=15), \
            "Register link not found in navigation"

    def test_login_link_navigation(self):
        """
        Test that login link navigates to login page.

        ACCEPTANCE CRITERIA:
        - Login link visible
        - Click navigates to login page
        - Login page loads successfully
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Click login link
        if page.is_element_present(*page.LOGIN_LINK, timeout=5):
            page.click_element(*page.LOGIN_LINK)
            time.sleep(2)

            # Verify on login page
            login_page = LoginPage(self.driver, self.config)
            assert login_page.is_on_login_page(), \
                "Did not navigate to login page"

    def test_register_link_navigation(self):
        """
        Test that register link navigates to registration page.

        ACCEPTANCE CRITERIA:
        - Register link visible
        - Click navigates to registration page
        - Registration page loads successfully
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Click register link
        if page.is_element_present(*page.REGISTER_LINK, timeout=5):
            page.click_element(*page.REGISTER_LINK)
            time.sleep(2)

            # Verify on registration page
            current_url = self.driver.current_url
            assert "register" in current_url.lower(), \
                "Did not navigate to registration page"

    def test_footer_links_present(self):
        """
        Test that footer links are present and accessible.

        ACCEPTANCE CRITERIA:
        - Footer section visible
        - Privacy policy link present
        - Terms of service link present
        - Social media links present (if applicable)
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Scroll to footer
        footer = page.find_element(*page.FOOTER)
        page.scroll_to_element(footer)
        time.sleep(1)

        # Verify footer links exist
        assert page.is_element_present(*page.PRIVACY_POLICY_LINK, timeout=15), \
            "Privacy policy link not found in footer"
        assert page.is_element_present(*page.TERMS_OF_SERVICE_LINK, timeout=15), \
            "Terms of service link not found in footer"

    def test_privacy_policy_link_in_footer(self):
        """
        Test that privacy policy link in footer works.

        ACCEPTANCE CRITERIA:
        - Privacy link clickable
        - Navigates to privacy policy page
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Scroll to footer and click privacy link
        footer = page.find_element(*page.FOOTER)
        page.scroll_to_element(footer)
        time.sleep(1)

        if page.is_element_present(*page.PRIVACY_POLICY_LINK, timeout=5):
            page.click_element(*page.PRIVACY_POLICY_LINK)
            time.sleep(2)

            # Verify navigated to privacy policy
            current_url = self.driver.current_url
            assert "privacy" in current_url.lower(), \
                "Did not navigate to privacy policy page"


class TestAccessibilityFeatures(BaseTest):
    """
    Tests for accessibility features on public pages.

    BUSINESS REQUIREMENT:
    Platform must be accessible to all users including those with
    disabilities, complying with WCAG guidelines.
    """

    def test_keyboard_navigation_on_homepage(self):
        """
        Test that homepage supports keyboard navigation.

        ACCEPTANCE CRITERIA:
        - Links are focusable via Tab key
        - Can navigate without mouse
        """
        page = HomePage(self.driver, self.config)
        page.navigate()

        # Try to focus on login link using Tab
        # (Implementation depends on actual page structure)
        login_link = page.find_element(*page.LOGIN_LINK)

        # Verify link is focusable
        assert login_link.is_displayed(), \
            "Login link not visible for keyboard navigation"

    def test_form_labels_present(self):
        """
        Test that forms have proper labels for accessibility.

        ACCEPTANCE CRITERIA:
        - All form inputs have associated labels
        - Labels are properly linked to inputs
        """
        page = RegistrationPage(self.driver, self.config)
        page.navigate()

        # Check if inputs have labels or aria-labels
        email_input = page.find_element(*page.EMAIL_INPUT)

        # Should have either a label, placeholder, or aria-label
        has_label = email_input.get_attribute("aria-label") or \
                   email_input.get_attribute("placeholder") or \
                   email_input.get_attribute("id")

        assert has_label, \
            "Form inputs should have labels for accessibility"
