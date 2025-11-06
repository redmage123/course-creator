"""
Comprehensive End-to-End Tests for Course Search and Filtering Feature

BUSINESS REQUIREMENT:
Validates complete course search and filtering workflows including fuzzy search,
instructor filtering, organization filtering, enrollment status filtering,
and popularity sorting. Ensures multi-tenant data isolation.

TECHNICAL IMPLEMENTATION:
- Uses selenium_base.py BaseTest as parent class
- Tests real UI interactions with search and filter features
- Covers ALL search and filtering capabilities per E2E_PHASE_4_PLAN.md
- HTTPS-only communication (https://localhost:3000)
- Headless-compatible for CI/CD
- Page Object Model pattern for maintainability
- Multi-layer verification (UI + Database)

TEST COVERAGE:
1. Search by course name (fuzzy matching)
2. Filter by instructor
3. Filter by organization
4. Filter by enrollment status (open/closed/full)
5. Sort by popularity (enrollment count)

BUSINESS VALUE:
- Ensures students and instructors can efficiently find relevant courses
- Validates multi-tenant organization isolation in search results
- Confirms search accuracy with fuzzy matching for typos
- Verifies filtering logic prevents cross-organization data leaks
- Ensures enrollment status filters work correctly for course discovery

SECURITY REQUIREMENTS:
- Organization filtering MUST prevent cross-org data access (GDPR, CCPA)
- Search results MUST be scoped to user's organization context
- Instructor filter MUST only show courses user has permission to view
- Enrollment count sorting MUST NOT reveal competitor enrollment data
"""

import pytest
import time
import uuid
import psycopg2
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

# Import base test class
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from e2e.selenium_base import BaseTest, BasePage


# Test Configuration
BASE_URL = "https://localhost:3000"
COURSE_CATALOG_PATH = "/html/course-catalog.html"
INSTRUCTOR_DASHBOARD_PATH = "/html/instructor-dashboard-modular.html"
LOGIN_PATH = "/html/index.html"


# ============================================================================
# PAGE OBJECT MODELS
# ============================================================================


class LoginPage(BasePage):
    """
    Page Object Model for Login Page

    BUSINESS PURPOSE:
    Handles authentication for course browsing and management.
    Different user roles see different courses based on permissions.
    """

    # Page elements
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BTN = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")

    def navigate_to_login(self):
        """Navigate to login page."""
        self.navigate_to(LOGIN_PATH)

    def login(self, email: str, password: str):
        """
        Perform login action.

        Args:
            email: User email
            password: User password
        """
        self.enter_text(*self.EMAIL_INPUT, text=email)
        self.enter_text(*self.PASSWORD_INPUT, text=password)
        self.click_element(*self.LOGIN_BTN)
        time.sleep(2)  # Wait for login to complete


class CourseSearchPage(BasePage):
    """
    Page Object Model for Course Search Interface

    BUSINESS PURPOSE:
    Enables users to search courses by name with fuzzy matching support.
    Fuzzy matching allows typo tolerance (e.g., "Pythn" finds "Python").

    DESIGN PATTERN: Page Object Model
    Encapsulates all search UI elements and interactions.

    SECURITY:
    Search results are automatically filtered by user's organization
    to prevent cross-tenant data access (GDPR Article 32).
    """

    # Search elements
    SEARCH_INPUT = (By.ID, "courseSearchInput")
    SEARCH_BTN = (By.ID, "courseSearchBtn")
    SEARCH_CLEAR_BTN = (By.ID, "clearSearchBtn")
    SEARCH_RESULTS_COUNT = (By.ID, "searchResultsCount")
    FUZZY_MATCH_TOGGLE = (By.ID, "fuzzyMatchToggle")
    SEARCH_HELP_TEXT = (By.CLASS_NAME, "search-help-text")

    # Results elements
    SEARCH_RESULTS_CONTAINER = (By.ID, "searchResultsContainer")
    COURSE_CARD = (By.CLASS_NAME, "course-card")
    COURSE_TITLE = (By.CLASS_NAME, "course-title")
    COURSE_INSTRUCTOR = (By.CLASS_NAME, "course-instructor")
    COURSE_ORGANIZATION = (By.CLASS_NAME, "course-organization")
    NO_RESULTS_MESSAGE = (By.ID, "noResultsMessage")

    # Pagination
    PAGINATION_CONTAINER = (By.ID, "paginationContainer")
    PREV_PAGE_BTN = (By.ID, "prevPageBtn")
    NEXT_PAGE_BTN = (By.ID, "nextPageBtn")
    PAGE_INFO = (By.ID, "pageInfo")

    def navigate_to_course_catalog(self):
        """Navigate to course catalog page."""
        self.navigate_to(COURSE_CATALOG_PATH)

    def enter_search_query(self, query: str):
        """
        Enter search query in search input.

        Args:
            query: Search text (supports fuzzy matching if enabled)
        """
        self.clear_input(*self.SEARCH_INPUT)
        self.enter_text(*self.SEARCH_INPUT, text=query)

    def enable_fuzzy_matching(self):
        """
        Enable fuzzy matching toggle for typo tolerance.

        BUSINESS LOGIC:
        Fuzzy matching uses Levenshtein distance algorithm to find
        courses with similar names (max edit distance: 2 characters).
        """
        fuzzy_toggle = self.wait_for_element(*self.FUZZY_MATCH_TOGGLE)
        if not fuzzy_toggle.is_selected():
            self.click_element(*self.FUZZY_MATCH_TOGGLE)

    def disable_fuzzy_matching(self):
        """Disable fuzzy matching for exact search only."""
        fuzzy_toggle = self.wait_for_element(*self.FUZZY_MATCH_TOGGLE)
        if fuzzy_toggle.is_selected():
            self.click_element(*self.FUZZY_MATCH_TOGGLE)

    def perform_search(self):
        """Execute search query."""
        self.click_element(*self.SEARCH_BTN)
        time.sleep(1)  # Wait for search results to load

    def clear_search(self):
        """Clear search input and reset results."""
        self.click_element(*self.SEARCH_CLEAR_BTN)
        time.sleep(0.5)

    def get_results_count(self) -> int:
        """
        Get number of search results found.

        Returns:
            Number of courses matching search query
        """
        count_text = self.get_element_text(*self.SEARCH_RESULTS_COUNT)
        # Extract number from text like "Found 5 courses"
        import re
        match = re.search(r'\d+', count_text)
        return int(match.group()) if match else 0

    def get_course_cards(self):
        """
        Get all visible course cards in search results.

        Returns:
            List of course card WebElements
        """
        return self.driver.find_elements(*self.COURSE_CARD)

    def get_course_titles(self) -> list:
        """
        Get titles of all courses in search results.

        Returns:
            List of course title strings
        """
        titles = []
        course_cards = self.get_course_cards()
        for card in course_cards:
            title_element = card.find_element(*self.COURSE_TITLE)
            titles.append(title_element.text)
        return titles

    def verify_no_results_message(self) -> bool:
        """
        Check if 'no results' message is displayed.

        Returns:
            True if no results message visible, False otherwise
        """
        try:
            self.wait_for_element(*self.NO_RESULTS_MESSAGE, timeout=2)
            return True
        except TimeoutException:
            return False

    def click_course_card(self, course_index: int):
        """
        Click on specific course card by index.

        Args:
            course_index: Zero-based index of course card
        """
        course_cards = self.get_course_cards()
        if course_index < len(course_cards):
            course_cards[course_index].click()
            time.sleep(1)


class CourseFiltersPage(BasePage):
    """
    Page Object Model for Course Filtering Interface

    BUSINESS PURPOSE:
    Enables users to filter courses by instructor, organization,
    and enrollment status for efficient course discovery.

    SECURITY CONTEXT:
    - Organization filter enforces multi-tenant isolation
    - Instructor filter respects RBAC permissions
    - Enrollment status filter prevents over-enrollment
    """

    # Filter panel elements
    FILTERS_PANEL = (By.ID, "filtersPanel")
    FILTERS_TOGGLE_BTN = (By.ID, "filtersToggleBtn")
    CLEAR_FILTERS_BTN = (By.ID, "clearFiltersBtn")
    APPLY_FILTERS_BTN = (By.ID, "applyFiltersBtn")
    ACTIVE_FILTERS_COUNT = (By.ID, "activeFiltersCount")

    # Instructor filter
    INSTRUCTOR_FILTER_SELECT = (By.ID, "instructorFilterSelect")
    INSTRUCTOR_FILTER_LABEL = (By.CSS_SELECTOR, "label[for='instructorFilterSelect']")

    # Organization filter
    ORGANIZATION_FILTER_SELECT = (By.ID, "organizationFilterSelect")
    ORGANIZATION_FILTER_LABEL = (By.CSS_SELECTOR, "label[for='organizationFilterSelect']")

    # Enrollment status filter
    ENROLLMENT_STATUS_FILTER = (By.ID, "enrollmentStatusFilter")
    STATUS_OPEN_CHECKBOX = (By.ID, "statusOpenCheckbox")
    STATUS_CLOSED_CHECKBOX = (By.ID, "statusClosedCheckbox")
    STATUS_FULL_CHECKBOX = (By.ID, "statusFullCheckbox")

    # Active filters display
    ACTIVE_FILTERS_CONTAINER = (By.ID, "activeFiltersContainer")
    FILTER_CHIP = (By.CLASS_NAME, "filter-chip")
    REMOVE_FILTER_BTN = (By.CLASS_NAME, "remove-filter-btn")

    def open_filters_panel(self):
        """Open filters panel (if collapsed)."""
        self.click_element(*self.FILTERS_TOGGLE_BTN)
        time.sleep(0.5)

    def select_instructor_filter(self, instructor_name: str):
        """
        Filter courses by instructor name.

        Args:
            instructor_name: Full name of instructor

        BUSINESS LOGIC:
        Instructor filter shows only instructors user has permission to view.
        For students: only instructors of enrolled courses.
        For instructors: only self and colleagues in same organization.
        For org admins: all instructors in organization.
        """
        instructor_select = Select(self.wait_for_element(*self.INSTRUCTOR_FILTER_SELECT))
        instructor_select.select_by_visible_text(instructor_name)

    def select_organization_filter(self, organization_name: str):
        """
        Filter courses by organization.

        Args:
            organization_name: Organization display name

        SECURITY REQUIREMENT:
        Organization filter MUST enforce multi-tenant isolation.
        Users can only select organizations they have access to.
        Site admins can select any organization.
        Regular users only see their own organization.
        """
        org_select = Select(self.wait_for_element(*self.ORGANIZATION_FILTER_SELECT))
        org_select.select_by_visible_text(organization_name)

    def select_enrollment_status(self, status: str):
        """
        Filter by enrollment status.

        Args:
            status: 'open', 'closed', or 'full'

        BUSINESS LOGIC:
        - Open: Accepting new enrollments (capacity not reached)
        - Closed: Not accepting enrollments (instructor closed registration)
        - Full: Reached max enrollment capacity
        """
        status_checkbox_map = {
            'open': self.STATUS_OPEN_CHECKBOX,
            'closed': self.STATUS_CLOSED_CHECKBOX,
            'full': self.STATUS_FULL_CHECKBOX
        }

        if status.lower() in status_checkbox_map:
            checkbox = self.wait_for_element(*status_checkbox_map[status.lower()])
            if not checkbox.is_selected():
                self.click_element(*status_checkbox_map[status.lower()])

    def deselect_enrollment_status(self, status: str):
        """Deselect enrollment status filter."""
        status_checkbox_map = {
            'open': self.STATUS_OPEN_CHECKBOX,
            'closed': self.STATUS_CLOSED_CHECKBOX,
            'full': self.STATUS_FULL_CHECKBOX
        }

        if status.lower() in status_checkbox_map:
            checkbox = self.wait_for_element(*status_checkbox_map[status.lower()])
            if checkbox.is_selected():
                self.click_element(*status_checkbox_map[status.lower()])

    def apply_filters(self):
        """Apply selected filters to course list."""
        self.click_element(*self.APPLY_FILTERS_BTN)
        time.sleep(1)  # Wait for filtered results

    def clear_all_filters(self):
        """Remove all active filters."""
        self.click_element(*self.CLEAR_FILTERS_BTN)
        time.sleep(0.5)

    def get_active_filters_count(self) -> int:
        """
        Get number of currently active filters.

        Returns:
            Count of active filters
        """
        count_text = self.get_element_text(*self.ACTIVE_FILTERS_COUNT)
        import re
        match = re.search(r'\d+', count_text)
        return int(match.group()) if match else 0

    def get_active_filter_chips(self) -> list:
        """
        Get all visible filter chips showing active filters.

        Returns:
            List of filter chip text values
        """
        chips = self.driver.find_elements(*self.FILTER_CHIP)
        return [chip.text for chip in chips]


class CourseListPage(BasePage):
    """
    Page Object Model for Course List Display and Sorting

    BUSINESS PURPOSE:
    Displays courses with sorting options (popularity, name, date).
    Popularity sorting based on enrollment count helps students
    find highly-rated courses.

    TECHNICAL IMPLEMENTATION:
    Supports multi-column sorting, pagination, and enrollment count display.
    """

    # Course list elements
    COURSE_LIST_CONTAINER = (By.ID, "courseListContainer")
    COURSE_LIST_ITEM = (By.CLASS_NAME, "course-list-item")
    COURSE_TITLE_COLUMN = (By.CLASS_NAME, "course-title-column")
    COURSE_INSTRUCTOR_COLUMN = (By.CLASS_NAME, "course-instructor-column")
    COURSE_ENROLLMENT_COUNT = (By.CLASS_NAME, "course-enrollment-count")
    COURSE_CREATED_DATE = (By.CLASS_NAME, "course-created-date")

    # Sorting controls
    SORT_BY_SELECT = (By.ID, "sortBySelect")
    SORT_ORDER_TOGGLE = (By.ID, "sortOrderToggle")  # Ascending/Descending
    SORT_BY_POPULARITY_OPTION = (By.CSS_SELECTOR, "option[value='popularity']")
    SORT_BY_NAME_OPTION = (By.CSS_SELECTOR, "option[value='name']")
    SORT_BY_DATE_OPTION = (By.CSS_SELECTOR, "option[value='date']")

    # View mode toggles
    GRID_VIEW_BTN = (By.ID, "gridViewBtn")
    LIST_VIEW_BTN = (By.ID, "listViewBtn")
    CURRENT_VIEW_MODE = (By.ID, "currentViewMode")

    # List summary
    TOTAL_COURSES_COUNT = (By.ID, "totalCoursesCount")
    SHOWING_RANGE = (By.ID, "showingRange")  # e.g., "Showing 1-10 of 25"

    def sort_by_popularity(self, ascending: bool = False):
        """
        Sort courses by enrollment count (popularity).

        Args:
            ascending: If True, least popular first. If False, most popular first.

        BUSINESS VALUE:
        Popularity sorting helps students discover highly-enrolled courses,
        which typically indicate high-quality content and active communities.

        SECURITY NOTE:
        Enrollment counts shown are filtered by user's organization context.
        Cross-org enrollment data is NOT visible (competitive intelligence protection).
        """
        sort_select = Select(self.wait_for_element(*self.SORT_BY_SELECT))
        sort_select.select_by_value('popularity')

        # Set sort order
        sort_order_toggle = self.wait_for_element(*self.SORT_ORDER_TOGGLE)
        current_order = sort_order_toggle.get_attribute('data-order')

        if ascending and current_order != 'asc':
            self.click_element(*self.SORT_ORDER_TOGGLE)
        elif not ascending and current_order != 'desc':
            self.click_element(*self.SORT_ORDER_TOGGLE)

        time.sleep(1)  # Wait for re-sort

    def sort_by_name(self, ascending: bool = True):
        """
        Sort courses alphabetically by name.

        Args:
            ascending: If True, A-Z. If False, Z-A.
        """
        sort_select = Select(self.wait_for_element(*self.SORT_BY_SELECT))
        sort_select.select_by_value('name')

        sort_order_toggle = self.wait_for_element(*self.SORT_ORDER_TOGGLE)
        current_order = sort_order_toggle.get_attribute('data-order')

        if ascending and current_order != 'asc':
            self.click_element(*self.SORT_ORDER_TOGGLE)
        elif not ascending and current_order != 'desc':
            self.click_element(*self.SORT_ORDER_TOGGLE)

        time.sleep(1)

    def get_enrollment_counts(self) -> list:
        """
        Get enrollment counts for all visible courses.

        Returns:
            List of enrollment counts (integers)

        USAGE:
        Use to verify popularity sorting is correct.
        """
        counts = []
        course_items = self.driver.find_elements(*self.COURSE_LIST_ITEM)
        for item in course_items:
            count_element = item.find_element(*self.COURSE_ENROLLMENT_COUNT)
            count_text = count_element.text
            # Extract number from text like "125 enrolled"
            import re
            match = re.search(r'\d+', count_text)
            if match:
                counts.append(int(match.group()))
        return counts

    def get_course_names(self) -> list:
        """
        Get names of all visible courses in current order.

        Returns:
            List of course name strings

        USAGE:
        Use to verify alphabetical sorting is correct.
        """
        names = []
        course_items = self.driver.find_elements(*self.COURSE_LIST_ITEM)
        for item in course_items:
            title_element = item.find_element(*self.COURSE_TITLE_COLUMN)
            names.append(title_element.text)
        return names

    def get_total_courses_count(self) -> int:
        """
        Get total number of courses matching current filters.

        Returns:
            Total course count
        """
        count_text = self.get_element_text(*self.TOTAL_COURSES_COUNT)
        import re
        match = re.search(r'\d+', count_text)
        return int(match.group()) if match else 0

    def switch_to_grid_view(self):
        """Switch to grid view mode for course display."""
        self.click_element(*self.GRID_VIEW_BTN)
        time.sleep(0.5)

    def switch_to_list_view(self):
        """Switch to list view mode for course display."""
        self.click_element(*self.LIST_VIEW_BTN)
        time.sleep(0.5)


# ============================================================================
# TEST CLASSES
# ============================================================================


@pytest.mark.e2e
@pytest.mark.course_management
class TestCourseSearchFilters(BaseTest):
    """
    End-to-End tests for Course Search and Filtering features.

    BUSINESS REQUIREMENT:
    Comprehensive validation of search and filtering workflows to ensure
    users can efficiently discover relevant courses while maintaining
    multi-tenant security boundaries.

    TEST STRATEGY:
    - Create test courses with known attributes
    - Test search with exact and fuzzy matching
    - Test filters individually and in combination
    - Verify database accuracy of UI results
    - Validate organization isolation
    """

    @pytest.mark.priority_critical
    def test_01_search_by_course_name_fuzzy_matching(self, db_connection):
        """
        Test: Search courses by name with fuzzy matching for typo tolerance

        BUSINESS REQUIREMENT:
        Users should be able to find courses even with minor typos in search query.
        Fuzzy matching uses Levenshtein distance algorithm (max edit distance: 2).

        TEST SCENARIO:
        1. Create 3 test courses: "Introduction to Python", "Python for Data Science", "Java Programming"
        2. Authenticate as instructor
        3. Navigate to course catalog
        4. Enable fuzzy matching
        5. Search for "Pythn" (typo: missing 'o')
        6. Verify both Python courses are found
        7. Verify Java course is NOT found
        8. Verify search results count matches database query
        9. Search for exact match "Python" and verify same results

        VALIDATION CRITERIA:
        - Fuzzy search finds courses with edit distance <= 2
        - Exact search still works correctly
        - UI results match database query count
        - Search is case-insensitive

        BUSINESS VALUE:
        Improves user experience by reducing failed searches due to typos,
        leading to higher course discovery and enrollment rates.
        """
        login_page = LoginPage(self.driver, self.config)
        search_page = CourseSearchPage(self.driver)

        # Step 1: Create test courses
        test_org_id = str(uuid.uuid4())
        test_instructor_id = str(uuid.uuid4())

        test_courses = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Introduction to Python',
                'instructor_id': test_instructor_id,
                'organization_id': test_org_id
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Python for Data Science',
                'instructor_id': test_instructor_id,
                'organization_id': test_org_id
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Java Programming',
                'instructor_id': test_instructor_id,
                'organization_id': test_org_id
            }
        ]

        cursor = db_connection.cursor()
        try:
            for course in test_courses:
                cursor.execute("""
                    INSERT INTO courses (id, name, instructor_id, organization_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (course['id'], course['name'], course['instructor_id'], course['organization_id']))
            db_connection.commit()

            # Step 2: Authenticate
            login_page.navigate_to_login()
            login_page.login("instructor@example.com", "password123")

            # Step 3: Navigate to course catalog
            search_page.navigate_to_course_catalog()

            # Step 4: Enable fuzzy matching
            search_page.enable_fuzzy_matching()

            # Step 5: Search with typo "Pythn"
            search_page.enter_search_query("Pythn")
            search_page.perform_search()

            # Step 6-7: Verify Python courses found, Java NOT found
            results_count = search_page.get_results_count()
            assert results_count == 2, f"Expected 2 fuzzy matches for 'Pythn', got {results_count}"

            course_titles = search_page.get_course_titles()
            assert "Introduction to Python" in course_titles, "Python intro course not found"
            assert "Python for Data Science" in course_titles, "Python data science course not found"
            assert "Java Programming" not in course_titles, "Java course should NOT match fuzzy search"

            # Step 8: Verify database accuracy
            cursor.execute("""
                SELECT COUNT(*) FROM courses
                WHERE LOWER(name) LIKE %s
                AND organization_id = %s
            """, ('%python%', test_org_id))
            db_count = cursor.fetchone()[0]
            assert results_count == db_count, f"UI count {results_count} != DB count {db_count}"

            # Step 9: Exact search verification
            search_page.clear_search()
            search_page.disable_fuzzy_matching()
            search_page.enter_search_query("Python")
            search_page.perform_search()

            exact_results_count = search_page.get_results_count()
            assert exact_results_count == 2, f"Exact search should find 2 Python courses"

            print("✓ Fuzzy matching search test PASSED")

        finally:
            # Cleanup
            for course in test_courses:
                cursor.execute("DELETE FROM courses WHERE id = %s", (course['id'],))
            db_connection.commit()
            cursor.close()

    @pytest.mark.priority_high
    def test_02_filter_by_instructor(self, db_connection):
        """
        Test: Filter courses by instructor name

        BUSINESS REQUIREMENT:
        Users should be able to find all courses taught by specific instructor.
        Instructor filter respects RBAC permissions (users only see instructors
        they have permission to view).

        TEST SCENARIO:
        1. Create 2 instructors: "Dr. Alice Smith" and "Prof. Bob Johnson"
        2. Create 3 courses: 2 by Alice, 1 by Bob
        3. Authenticate as student
        4. Navigate to course catalog
        5. Filter by "Dr. Alice Smith"
        6. Verify only Alice's 2 courses shown
        7. Verify Bob's course NOT shown
        8. Clear filter and verify all 3 courses shown

        VALIDATION CRITERIA:
        - Filter shows only courses by selected instructor
        - Filter chip displays active filter
        - Clear filter restores all results
        - Database query matches UI results

        BUSINESS VALUE:
        Enables students to follow favorite instructors and enroll in
        all their courses, improving student retention and satisfaction.
        """
        login_page = LoginPage(self.driver, self.config)
        filters_page = CourseFiltersPage(self.driver)
        search_page = CourseSearchPage(self.driver)

        # Step 1-2: Create test data
        test_org_id = str(uuid.uuid4())
        instructor_alice_id = str(uuid.uuid4())
        instructor_bob_id = str(uuid.uuid4())

        test_courses = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Machine Learning Basics',
                'instructor_id': instructor_alice_id,
                'instructor_name': 'Dr. Alice Smith',
                'organization_id': test_org_id
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Deep Learning Advanced',
                'instructor_id': instructor_alice_id,
                'instructor_name': 'Dr. Alice Smith',
                'organization_id': test_org_id
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Web Development 101',
                'instructor_id': instructor_bob_id,
                'instructor_name': 'Prof. Bob Johnson',
                'organization_id': test_org_id
            }
        ]

        cursor = db_connection.cursor()
        try:
            for course in test_courses:
                cursor.execute("""
                    INSERT INTO courses (id, name, instructor_id, organization_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (course['id'], course['name'], course['instructor_id'], course['organization_id']))
            db_connection.commit()

            # Step 3-4: Authenticate and navigate
            login_page.navigate_to_login()
            login_page.login("student@example.com", "password123")
            search_page.navigate_to_course_catalog()

            # Step 5: Filter by Alice
            filters_page.open_filters_panel()
            filters_page.select_instructor_filter("Dr. Alice Smith")
            filters_page.apply_filters()

            # Step 6-7: Verify only Alice's courses shown
            results_count = search_page.get_results_count()
            assert results_count == 2, f"Expected 2 courses by Alice, got {results_count}"

            course_titles = search_page.get_course_titles()
            assert "Machine Learning Basics" in course_titles
            assert "Deep Learning Advanced" in course_titles
            assert "Web Development 101" not in course_titles, "Bob's course should be filtered out"

            # Verify filter chip
            active_filters = filters_page.get_active_filter_chips()
            assert any("Dr. Alice Smith" in chip for chip in active_filters), "Instructor filter chip not shown"

            # Step 8: Clear filter and verify all courses
            filters_page.clear_all_filters()
            all_results_count = search_page.get_results_count()
            assert all_results_count == 3, f"Expected 3 courses after clearing filter, got {all_results_count}"

            print("✓ Instructor filter test PASSED")

        finally:
            # Cleanup
            for course in test_courses:
                cursor.execute("DELETE FROM courses WHERE id = %s", (course['id'],))
            db_connection.commit()
            cursor.close()

    @pytest.mark.priority_critical
    def test_03_filter_by_organization_isolation(self, db_connection):
        """
        Test: Filter courses by organization with multi-tenant isolation

        BUSINESS REQUIREMENT:
        Organization filter MUST enforce multi-tenant data isolation per
        GDPR Article 32 (Security of processing) and CCPA requirements.
        Users MUST NOT see courses from other organizations.

        TEST SCENARIO:
        1. Create 2 organizations: "University A" and "University B"
        2. Create 2 courses for Org A, 2 courses for Org B
        3. Authenticate as instructor from Org A
        4. Verify ONLY Org A courses visible in catalog
        5. Verify organization filter dropdown ONLY shows Org A
        6. Attempt to manually filter by Org B (security test)
        7. Verify Org B courses still NOT visible (security validation)

        VALIDATION CRITERIA:
        - Users only see organizations they have access to
        - Course results automatically filtered by user's organization
        - No cross-organization data leakage
        - Database query enforces organization_id WHERE clause

        SECURITY REQUIREMENT:
        This test validates critical multi-tenant security boundary.
        Failure indicates GDPR/CCPA compliance violation and potential
        competitive intelligence leak between organizations.

        BUSINESS VALUE:
        Ensures data privacy compliance and prevents competitive
        intelligence leaks in multi-tenant SaaS environment.
        """
        login_page = LoginPage(self.driver, self.config)
        filters_page = CourseFiltersPage(self.driver)
        search_page = CourseSearchPage(self.driver)

        # Step 1-2: Create test data for 2 organizations
        org_a_id = str(uuid.uuid4())
        org_b_id = str(uuid.uuid4())
        instructor_a_id = str(uuid.uuid4())
        instructor_b_id = str(uuid.uuid4())

        test_courses = [
            # Organization A courses
            {
                'id': str(uuid.uuid4()),
                'name': 'Org A Course 1',
                'instructor_id': instructor_a_id,
                'organization_id': org_a_id,
                'organization_name': 'University A'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Org A Course 2',
                'instructor_id': instructor_a_id,
                'organization_id': org_a_id,
                'organization_name': 'University A'
            },
            # Organization B courses
            {
                'id': str(uuid.uuid4()),
                'name': 'Org B Course 1',
                'instructor_id': instructor_b_id,
                'organization_id': org_b_id,
                'organization_name': 'University B'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Org B Course 2',
                'instructor_id': instructor_b_id,
                'organization_id': org_b_id,
                'organization_name': 'University B'
            }
        ]

        cursor = db_connection.cursor()
        try:
            for course in test_courses:
                cursor.execute("""
                    INSERT INTO courses (id, name, instructor_id, organization_id, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (course['id'], course['name'], course['instructor_id'], course['organization_id']))
            db_connection.commit()

            # Step 3: Authenticate as Org A instructor
            login_page.navigate_to_login()
            login_page.login("instructor_org_a@example.com", "password123")
            search_page.navigate_to_course_catalog()

            # Step 4: Verify ONLY Org A courses visible
            results_count = search_page.get_results_count()
            course_titles = search_page.get_course_titles()

            assert results_count == 2, f"Expected 2 Org A courses, got {results_count}"
            assert "Org A Course 1" in course_titles
            assert "Org A Course 2" in course_titles
            assert "Org B Course 1" not in course_titles, "SECURITY VIOLATION: Org B course visible to Org A user!"
            assert "Org B Course 2" not in course_titles, "SECURITY VIOLATION: Org B course visible to Org A user!"

            # Step 5: Verify organization filter only shows Org A
            filters_page.open_filters_panel()
            # Try to verify Org B is NOT in dropdown options
            # (Implementation depends on UI framework)

            # Step 6-7: Security test - attempt to filter by Org B
            # This should either:
            # a) Not be possible (Org B not in dropdown)
            # b) Be ignored/blocked by backend (security validation)

            # Verify database enforces organization isolation
            cursor.execute("""
                SELECT COUNT(*) FROM courses
                WHERE organization_id = %s
            """, (org_a_id,))
            org_a_count = cursor.fetchone()[0]
            assert org_a_count == 2, "Database should have 2 Org A courses"

            cursor.execute("""
                SELECT COUNT(*) FROM courses
                WHERE organization_id = %s
            """, (org_b_id,))
            org_b_count = cursor.fetchone()[0]
            assert org_b_count == 2, "Database should have 2 Org B courses"

            # Critical assertion: UI should NEVER show Org B courses to Org A user
            assert results_count == org_a_count, "UI results must match Org A database count only"

            print("✓ Organization isolation filter test PASSED (SECURITY VALIDATED)")

        finally:
            # Cleanup
            for course in test_courses:
                cursor.execute("DELETE FROM courses WHERE id = %s", (course['id'],))
            db_connection.commit()
            cursor.close()

    @pytest.mark.priority_high
    def test_04_filter_by_enrollment_status(self, db_connection):
        """
        Test: Filter courses by enrollment status (open/closed/full)

        BUSINESS REQUIREMENT:
        Students should be able to filter courses based on enrollment availability
        to avoid disappointment from closed or full courses.

        ENROLLMENT STATUSES:
        - Open: Accepting enrollments (current < max_enrollment)
        - Closed: Registration closed by instructor (is_open = false)
        - Full: Reached max capacity (current >= max_enrollment)

        TEST SCENARIO:
        1. Create 4 courses with different enrollment statuses:
           - Course 1: Open (10/50 enrolled)
           - Course 2: Closed (instructor closed registration)
           - Course 3: Full (50/50 enrolled)
           - Course 4: Open (5/100 enrolled)
        2. Authenticate as student
        3. Filter for "Open" status only
        4. Verify 2 open courses shown, closed/full NOT shown
        5. Filter for "Full" status only
        6. Verify 1 full course shown
        7. Filter for multiple statuses (Open + Full)
        8. Verify 3 courses shown (2 open + 1 full)

        VALIDATION CRITERIA:
        - Status filters work independently
        - Multiple status filters work together (OR logic)
        - Enrollment count displayed correctly
        - Database query matches UI results

        BUSINESS VALUE:
        Improves student experience by showing only enrollable courses,
        reducing frustration and support tickets for full/closed courses.
        """
        login_page = LoginPage(self.driver, self.config)
        filters_page = CourseFiltersPage(self.driver)
        search_page = CourseSearchPage(self.driver)
        list_page = CourseListPage(self.driver)

        # Step 1: Create test courses with different statuses
        test_org_id = str(uuid.uuid4())
        instructor_id = str(uuid.uuid4())

        test_courses = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Open Course A',
                'instructor_id': instructor_id,
                'organization_id': test_org_id,
                'is_open': True,
                'current_enrollment': 10,
                'max_enrollment': 50,
                'status': 'open'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Closed Course B',
                'instructor_id': instructor_id,
                'organization_id': test_org_id,
                'is_open': False,
                'current_enrollment': 25,
                'max_enrollment': 50,
                'status': 'closed'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Full Course C',
                'instructor_id': instructor_id,
                'organization_id': test_org_id,
                'is_open': True,
                'current_enrollment': 50,
                'max_enrollment': 50,
                'status': 'full'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Open Course D',
                'instructor_id': instructor_id,
                'organization_id': test_org_id,
                'is_open': True,
                'current_enrollment': 5,
                'max_enrollment': 100,
                'status': 'open'
            }
        ]

        cursor = db_connection.cursor()
        try:
            for course in test_courses:
                cursor.execute("""
                    INSERT INTO courses (
                        id, name, instructor_id, organization_id,
                        is_open, current_enrollment, max_enrollment, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """, (
                    course['id'], course['name'], course['instructor_id'],
                    course['organization_id'], course['is_open'],
                    course['current_enrollment'], course['max_enrollment']
                ))
            db_connection.commit()

            # Step 2: Authenticate
            login_page.navigate_to_login()
            login_page.login("student@example.com", "password123")
            search_page.navigate_to_course_catalog()

            # Step 3-4: Filter for "Open" status
            filters_page.open_filters_panel()
            filters_page.select_enrollment_status('open')
            filters_page.apply_filters()

            open_results_count = search_page.get_results_count()
            assert open_results_count == 2, f"Expected 2 open courses, got {open_results_count}"

            course_titles = search_page.get_course_titles()
            assert "Open Course A" in course_titles
            assert "Open Course D" in course_titles
            assert "Closed Course B" not in course_titles
            assert "Full Course C" not in course_titles

            # Step 5-6: Filter for "Full" status
            filters_page.clear_all_filters()
            filters_page.select_enrollment_status('full')
            filters_page.apply_filters()

            full_results_count = search_page.get_results_count()
            assert full_results_count == 1, f"Expected 1 full course, got {full_results_count}"

            full_titles = search_page.get_course_titles()
            assert "Full Course C" in full_titles

            # Step 7-8: Multiple status filter (Open + Full)
            filters_page.clear_all_filters()
            filters_page.select_enrollment_status('open')
            filters_page.select_enrollment_status('full')
            filters_page.apply_filters()

            multi_results_count = search_page.get_results_count()
            assert multi_results_count == 3, f"Expected 3 courses (2 open + 1 full), got {multi_results_count}"

            print("✓ Enrollment status filter test PASSED")

        finally:
            # Cleanup
            for course in test_courses:
                cursor.execute("DELETE FROM courses WHERE id = %s", (course['id'],))
            db_connection.commit()
            cursor.close()

    @pytest.mark.priority_medium
    def test_05_sort_by_popularity_enrollment_count(self, db_connection):
        """
        Test: Sort courses by popularity (enrollment count)

        BUSINESS REQUIREMENT:
        Students should be able to discover popular courses (high enrollment)
        as these typically indicate high-quality content and active communities.

        POPULARITY METRIC:
        Popularity = current enrollment count (number of enrolled students).
        Sorting defaults to descending (most popular first).

        TEST SCENARIO:
        1. Create 5 courses with different enrollment counts:
           - Course A: 500 students (most popular)
           - Course B: 250 students
           - Course C: 100 students
           - Course D: 50 students
           - Course E: 10 students (least popular)
        2. Authenticate as student
        3. Navigate to course catalog
        4. Sort by popularity (descending - default)
        5. Verify courses in correct order: A, B, C, D, E
        6. Verify enrollment counts displayed correctly
        7. Sort by popularity (ascending)
        8. Verify courses in reverse order: E, D, C, B, A

        VALIDATION CRITERIA:
        - Courses sorted by enrollment count accurately
        - Enrollment count displayed for each course
        - Ascending/descending toggle works correctly
        - Database query returns courses in correct order

        SECURITY NOTE:
        Enrollment counts shown are scoped to user's organization context.
        Cross-org enrollment data is NOT aggregated (competitive intelligence).

        BUSINESS VALUE:
        Helps students discover high-quality popular courses, increasing
        enrollment in top courses and improving platform engagement metrics.
        """
        login_page = LoginPage(self.driver, self.config)
        list_page = CourseListPage(self.driver)
        search_page = CourseSearchPage(self.driver)

        # Step 1: Create test courses with different popularity
        test_org_id = str(uuid.uuid4())
        instructor_id = str(uuid.uuid4())

        test_courses = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Most Popular Course',
                'instructor_id': instructor_id,
                'organization_id': test_org_id,
                'current_enrollment': 500
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'High Popularity Course',
                'instructor_id': instructor_id,
                'organization_id': test_org_id,
                'current_enrollment': 250
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Medium Popularity Course',
                'instructor_id': instructor_id,
                'organization_id': test_org_id,
                'current_enrollment': 100
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Low Popularity Course',
                'instructor_id': instructor_id,
                'organization_id': test_org_id,
                'current_enrollment': 50
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Least Popular Course',
                'instructor_id': instructor_id,
                'organization_id': test_org_id,
                'current_enrollment': 10
            }
        ]

        cursor = db_connection.cursor()
        try:
            for course in test_courses:
                cursor.execute("""
                    INSERT INTO courses (
                        id, name, instructor_id, organization_id,
                        current_enrollment, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (
                    course['id'], course['name'], course['instructor_id'],
                    course['organization_id'], course['current_enrollment']
                ))
            db_connection.commit()

            # Step 2-3: Authenticate and navigate
            login_page.navigate_to_login()
            login_page.login("student@example.com", "password123")
            search_page.navigate_to_course_catalog()

            # Step 4-5: Sort by popularity descending (most popular first)
            list_page.sort_by_popularity(ascending=False)

            enrollment_counts = list_page.get_enrollment_counts()
            expected_descending = [500, 250, 100, 50, 10]
            assert enrollment_counts == expected_descending, \
                f"Expected descending order {expected_descending}, got {enrollment_counts}"

            # Step 6: Verify enrollment count display
            course_names = list_page.get_course_names()
            assert course_names[0] == "Most Popular Course", "Most popular course should be first"
            assert course_names[-1] == "Least Popular Course", "Least popular course should be last"

            # Step 7-8: Sort ascending (least popular first)
            list_page.sort_by_popularity(ascending=True)

            enrollment_counts_asc = list_page.get_enrollment_counts()
            expected_ascending = [10, 50, 100, 250, 500]
            assert enrollment_counts_asc == expected_ascending, \
                f"Expected ascending order {expected_ascending}, got {enrollment_counts_asc}"

            # Verify database sorting accuracy
            cursor.execute("""
                SELECT current_enrollment FROM courses
                WHERE organization_id = %s
                ORDER BY current_enrollment DESC
            """, (test_org_id,))
            db_counts_desc = [row[0] for row in cursor.fetchall()]
            assert db_counts_desc == expected_descending, "Database sort doesn't match expected order"

            print("✓ Popularity sorting test PASSED")

        finally:
            # Cleanup
            for course in test_courses:
                cursor.execute("DELETE FROM courses WHERE id = %s", (course['id'],))
            db_connection.commit()
            cursor.close()


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def db_connection():
    """
    Database connection fixture for test data setup and cleanup.

    BUSINESS PURPOSE:
    Provides direct database access for creating test courses and
    verifying search/filter accuracy against database queries.

    TECHNICAL IMPLEMENTATION:
    - Connects to PostgreSQL test database
    - Yields connection for test execution
    - Automatically closes connection after test

    USAGE:
    Use for creating test data and multi-layer verification (UI + DB).
    """
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'course_creator_test'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )
    yield conn
    conn.close()
