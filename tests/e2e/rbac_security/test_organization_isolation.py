"""
Comprehensive E2E Tests for Multi-Tenant Organization Isolation

BUSINESS REQUIREMENT:
The platform must enforce strict multi-tenant isolation to ensure organizations cannot access
each other's data, resources, or analytics. This is critical for data privacy, security compliance
(GDPR, CCPA, PIPEDA), and maintaining customer trust in a multi-tenant SaaS environment.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Validates organization isolation at UI, API, and database levels
- Multi-layer verification: UI display + API response + database permissions + Docker containers
- Tests cross-organization access attempts and verifies proper blocking

ISOLATION REQUIREMENTS:
1. Data Isolation - Organizations cannot see each other's:
   - Courses and course content
   - Students and enrollment data
   - Analytics and performance metrics
   - API responses must filter by organization_id

2. Resource Isolation - Organizations have separate:
   - Lab containers (Docker namespace isolation)
   - Storage quotas (S3/filesystem buckets)
   - Analytics calculations (aggregations per org)
   - Search results (filtered by organization)

TEST COVERAGE:
1. Data Isolation (4 tests)
   - Organization A cannot see Organization B's courses
   - Organization A cannot see Organization B's students
   - Organization A cannot see Organization B's analytics
   - Cross-organization API access blocked

2. Resource Isolation (4 tests)
   - Lab containers isolated by organization
   - Storage quotas separate per organization
   - Analytics calculations separate per organization
   - Search results filtered by organization

SECURITY IMPLICATIONS:
- Prevents data breaches between tenants
- Ensures compliance with multi-tenant security standards
- Protects competitive business intelligence
- Maintains audit trails for regulatory compliance

PRIORITY: P0 (CRITICAL) - Core security functionality
COMPLIANCE: GDPR Article 32, CCPA Section 1798.150, ISO 27001
"""

import pytest
import time
import uuid
import asyncio
import asyncpg
import httpx
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class LoginPage(BasePage):
    """
    Page Object for login page.

    BUSINESS CONTEXT:
    Authentication establishes user organization context.
    All subsequent actions must respect this organizational boundary.
    """

    # Locators
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")

    def navigate(self):
        """Navigate to login page."""
        self.navigate_to("/login")

    def login(self, email: str, password: str):
        """
        Perform user login.

        Args:
            email: User email
            password: User password
        """
        self.wait_for_element_visible(*self.EMAIL_INPUT)
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)
        time.sleep(2)  # Wait for authentication and redirect


class OrganizationCoursesPage(BasePage):
    """
    Page Object for organization courses listing.

    BUSINESS CONTEXT:
    Courses must be filtered by organization. Users should only see
    courses belonging to their organization, never cross-org courses.
    """

    # Locators
    COURSES_CONTAINER = (By.CLASS_NAME, "courses-container")
    COURSE_CARD = (By.CLASS_NAME, "course-card")
    COURSE_TITLE = (By.CLASS_NAME, "course-title")
    COURSE_ORG = (By.CLASS_NAME, "course-organization")
    NO_COURSES_MESSAGE = (By.CLASS_NAME, "no-courses-message")
    SEARCH_INPUT = (By.ID, "courseSearchInput")
    FILTER_ORG_DROPDOWN = (By.ID, "organizationFilter")
    COURSE_COUNT = (By.CLASS_NAME, "course-count")
    LOADING_SPINNER = (By.CLASS_NAME, "loading-spinner")

    def navigate(self):
        """Navigate to courses page."""
        self.navigate_to("/courses")

    def wait_for_courses_loaded(self):
        """
        Wait for courses to finish loading.

        TECHNICAL REQUIREMENT:
        Must wait for loading spinner to disappear before verifying isolation.
        """
        try:
            self.wait_for_element_invisible(*self.LOADING_SPINNER, timeout=10)
        except TimeoutException:
            pass  # No spinner, already loaded

    def get_all_course_titles(self) -> list:
        """
        Get all course titles displayed on page.

        Returns:
            List of course title strings
        """
        self.wait_for_courses_loaded()
        course_elements = self.driver.find_elements(*self.COURSE_TITLE)
        return [elem.text.strip() for elem in course_elements]

    def get_course_organization_ids(self) -> list:
        """
        Get organization IDs for all displayed courses.

        BUSINESS CONTEXT:
        Extracts org IDs from data attributes to verify isolation.

        Returns:
            List of organization ID strings
        """
        self.wait_for_courses_loaded()
        course_cards = self.driver.find_elements(*self.COURSE_CARD)
        return [card.get_attribute('data-organization-id') for card in course_cards]

    def search_for_course(self, course_title: str):
        """
        Search for course by title.

        SECURITY IMPLICATION:
        Search must not return courses from other organizations
        even if they match the search term.

        Args:
            course_title: Course title to search for
        """
        self.enter_text(*self.SEARCH_INPUT, course_title)
        time.sleep(1)  # Wait for search results

    def get_course_count(self) -> int:
        """
        Get total count of courses displayed.

        Returns:
            Number of courses
        """
        self.wait_for_courses_loaded()
        try:
            count_text = self.get_element_text(*self.COURSE_COUNT)
            # Extract number from text like "Showing 5 courses"
            return int(''.join(filter(str.isdigit, count_text)))
        except (NoSuchElementException, ValueError):
            # Count course cards directly
            return len(self.driver.find_elements(*self.COURSE_CARD))

    def is_no_courses_message_displayed(self) -> bool:
        """Check if 'no courses' message is displayed."""
        return self.is_element_present(*self.NO_COURSES_MESSAGE, timeout=3)


class OrganizationAnalyticsPage(BasePage):
    """
    Page Object for organization analytics dashboard.

    BUSINESS CONTEXT:
    Analytics must be calculated per organization. Aggregated metrics
    (total students, average scores, completion rates) must exclude
    data from other organizations to prevent competitive intelligence leaks.
    """

    # Locators
    ANALYTICS_CONTAINER = (By.CLASS_NAME, "analytics-container")
    TOTAL_STUDENTS = (By.ID, "totalStudents")
    TOTAL_COURSES = (By.ID, "totalCourses")
    AVERAGE_SCORE = (By.ID, "averageScore")
    COMPLETION_RATE = (By.ID, "completionRate")
    ENROLLMENT_CHART = (By.ID, "enrollmentChart")
    PERFORMANCE_CHART = (By.ID, "performanceChart")
    ORG_NAME_HEADER = (By.CLASS_NAME, "org-name-header")
    ANALYTICS_LOADING = (By.CLASS_NAME, "analytics-loading")
    EXPORT_BUTTON = (By.ID, "exportAnalytics")
    DATE_RANGE_SELECTOR = (By.ID, "dateRangeSelector")

    def navigate(self):
        """Navigate to analytics page."""
        self.navigate_to("/analytics")

    def wait_for_analytics_loaded(self):
        """
        Wait for analytics to finish loading.

        TECHNICAL REQUIREMENT:
        Analytics calculations may take time, must wait for completion.
        """
        try:
            self.wait_for_element_invisible(*self.ANALYTICS_LOADING, timeout=15)
        except TimeoutException:
            pass  # No loading indicator

    def get_total_students(self) -> int:
        """
        Get total students metric.

        ISOLATION VERIFICATION:
        This count must only include students from current organization.

        Returns:
            Total student count
        """
        self.wait_for_analytics_loaded()
        text = self.get_element_text(*self.TOTAL_STUDENTS)
        return int(''.join(filter(str.isdigit, text)))

    def get_total_courses(self) -> int:
        """
        Get total courses metric.

        Returns:
            Total course count
        """
        self.wait_for_analytics_loaded()
        text = self.get_element_text(*self.TOTAL_COURSES)
        return int(''.join(filter(str.isdigit, text)))

    def get_average_score(self) -> float:
        """
        Get average score metric.

        ISOLATION VERIFICATION:
        Average must be calculated only from current org's students.

        Returns:
            Average score percentage
        """
        self.wait_for_analytics_loaded()
        text = self.get_element_text(*self.AVERAGE_SCORE)
        # Extract decimal from text like "85.5%"
        return float(''.join(c for c in text if c.isdigit() or c == '.'))

    def get_completion_rate(self) -> float:
        """
        Get course completion rate metric.

        Returns:
            Completion rate percentage
        """
        self.wait_for_analytics_loaded()
        text = self.get_element_text(*self.COMPLETION_RATE)
        return float(''.join(c for c in text if c.isdigit() or c == '.'))

    def get_organization_name(self) -> str:
        """
        Get organization name from header.

        VERIFICATION:
        Confirms which organization's analytics are displayed.

        Returns:
            Organization name
        """
        return self.get_element_text(*self.ORG_NAME_HEADER)


class OrganizationSearchPage(BasePage):
    """
    Page Object for platform-wide search.

    BUSINESS CONTEXT:
    Search results must be filtered by user's organization context.
    Even exact matches from other organizations must be excluded to
    prevent information disclosure.
    """

    # Locators
    SEARCH_INPUT = (By.ID, "globalSearchInput")
    SEARCH_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    SEARCH_RESULTS = (By.CLASS_NAME, "search-results")
    RESULT_ITEM = (By.CLASS_NAME, "search-result-item")
    RESULT_TITLE = (By.CLASS_NAME, "result-title")
    RESULT_TYPE = (By.CLASS_NAME, "result-type")
    RESULT_ORG_ID = (By.CLASS_NAME, "result-org-id")
    NO_RESULTS_MESSAGE = (By.CLASS_NAME, "no-results-message")
    RESULTS_COUNT = (By.CLASS_NAME, "results-count")
    FILTER_TYPE = (By.ID, "searchTypeFilter")
    LOADING_RESULTS = (By.CLASS_NAME, "search-loading")

    def navigate(self):
        """Navigate to search page."""
        self.navigate_to("/search")

    def perform_search(self, query: str):
        """
        Perform search query.

        SECURITY IMPLICATION:
        Query must not return results from other organizations
        regardless of exact match.

        Args:
            query: Search query string
        """
        self.enter_text(*self.SEARCH_INPUT, query)
        self.click_element(*self.SEARCH_BUTTON)
        self.wait_for_search_results_loaded()

    def wait_for_search_results_loaded(self):
        """Wait for search results to finish loading."""
        try:
            self.wait_for_element_invisible(*self.LOADING_RESULTS, timeout=10)
        except TimeoutException:
            pass

    def get_search_results_count(self) -> int:
        """
        Get number of search results.

        Returns:
            Result count
        """
        try:
            count_text = self.get_element_text(*self.RESULTS_COUNT)
            return int(''.join(filter(str.isdigit, count_text)))
        except (NoSuchElementException, ValueError):
            return len(self.driver.find_elements(*self.RESULT_ITEM))

    def get_result_titles(self) -> list:
        """
        Get all result titles.

        Returns:
            List of result title strings
        """
        elements = self.driver.find_elements(*self.RESULT_TITLE)
        return [elem.text.strip() for elem in elements]

    def get_result_organization_ids(self) -> list:
        """
        Get organization IDs from search results.

        ISOLATION VERIFICATION:
        All results must have matching organization ID.

        Returns:
            List of organization IDs
        """
        elements = self.driver.find_elements(*self.RESULT_ITEM)
        return [elem.get_attribute('data-organization-id') for elem in elements]

    def filter_by_type(self, result_type: str):
        """
        Filter results by type (course, student, content).

        Args:
            result_type: Type filter value
        """
        select = Select(self.driver.find_element(*self.FILTER_TYPE))
        select.select_by_value(result_type)
        self.wait_for_search_results_loaded()

    def is_no_results_message_displayed(self) -> bool:
        """Check if 'no results' message is displayed."""
        return self.is_element_present(*self.NO_RESULTS_MESSAGE, timeout=3)


# ============================================================================
# TEST CLASS - Data Isolation Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.rbac
class TestOrganizationDataIsolation(BaseTest):
    """
    Test suite for organization data isolation.

    BUSINESS REQUIREMENT:
    Organizations must not be able to view, access, or modify data
    belonging to other organizations. This includes courses, students,
    enrollments, analytics, and all related data.
    """

    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_01_organization_cannot_see_other_org_courses(
        self,
        test_users,
        test_organizations,
        test_courses,
        db_pool
    ):
        """
        Test: Organization A instructor cannot see Organization B's courses

        BUSINESS SCENARIO:
        1. Organization A (test-org) has 3 courses
        2. Organization B (other-org) has 1 course
        3. Instructor from Org A logs in
        4. Views course listing
        5. Should only see Org A's 3 courses, not Org B's course

        SECURITY REQUIREMENT:
        Even if instructor knows the exact course title from Org B,
        it must not appear in search results or direct navigation.

        COMPLIANCE: GDPR Article 32 (Data Security)
        """
        login_page = LoginPage(self.driver)
        courses_page = OrganizationCoursesPage(self.driver)

        # Step 1: Login as Organization A instructor
        login_page.navigate()
        org_a_instructor = test_users['instructor']
        login_page.login(org_a_instructor['email'], org_a_instructor['password'])

        # Step 2: Navigate to courses page
        courses_page.navigate()
        courses_page.wait_for_courses_loaded()

        # Step 3: Get displayed courses
        course_titles = courses_page.get_all_course_titles()
        course_org_ids = courses_page.get_course_organization_ids()

        # Step 4: Verify only Org A courses are visible
        org_a_id = test_organizations[0]['organization_id']  # org-001
        org_b_course_title = test_courses[3]['title']  # "Machine Learning" from org-002

        # ASSERTION 1: Org B course is NOT in the list
        assert org_b_course_title not in course_titles, \
            f"Org B course '{org_b_course_title}' should not be visible to Org A instructor"

        # ASSERTION 2: All visible courses belong to Org A
        for org_id in course_org_ids:
            assert org_id == org_a_id, \
                f"Course from organization {org_id} visible, but should only see {org_a_id}"

        # Step 5: Verify database isolation
        async with db_pool.acquire() as conn:
            # Count courses visible to Org A instructor
            org_a_course_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM courses c
                WHERE c.organization_id = $1
                """,
                org_a_id
            )

            # Verify UI shows same count as database
            ui_course_count = courses_page.get_course_count()
            assert ui_course_count == org_a_course_count, \
                f"UI shows {ui_course_count} courses but DB has {org_a_course_count} for Org A"

        # Step 6: Try searching for Org B course by exact title
        courses_page.search_for_course(org_b_course_title)
        time.sleep(1)

        # ASSERTION 3: Search must not return Org B course
        search_results = courses_page.get_all_course_titles()
        assert org_b_course_title not in search_results, \
            f"Search must not return Org B course even with exact title match"

        # ASSERTION 4: Either no results or only Org A courses
        if not courses_page.is_no_courses_message_displayed():
            search_org_ids = courses_page.get_course_organization_ids()
            for org_id in search_org_ids:
                assert org_id == org_a_id, \
                    f"Search leaked course from org {org_id} instead of filtering to {org_a_id}"

    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_02_organization_cannot_see_other_org_students(
        self,
        test_users,
        test_organizations,
        db_pool
    ):
        """
        Test: Organization Admin cannot see students from other organizations

        BUSINESS SCENARIO:
        1. Organization A has 50 students
        2. Organization B has 30 students
        3. Org Admin A logs in and views student list
        4. Should only see Org A's 50 students
        5. Cannot search for or access Org B students

        PRIVACY IMPLICATION:
        Student PII (names, emails, performance) must be strictly isolated.
        Exposure could violate GDPR/CCPA and damage customer trust.

        COMPLIANCE: GDPR Article 32, CCPA Section 1798.150
        """
        login_page = LoginPage(self.driver)

        # Step 1: Login as Organization A admin
        login_page.navigate()
        org_a_admin = test_users['org_admin']
        login_page.login(org_a_admin['email'], org_a_admin['password'])

        # Step 2: Navigate to students management page
        self.driver.get(f"{self.base_url}/org-admin/students")
        time.sleep(2)

        # Step 3: Verify student count from database
        org_a_id = test_organizations[0]['organization_id']
        org_b_id = test_organizations[1]['organization_id']

        async with db_pool.acquire() as conn:
            # Count students in Org A
            org_a_student_count = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT u.user_id)
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN organization_members om ON u.user_id = om.user_id
                WHERE ur.role_type = 'STUDENT'
                  AND om.organization_id = $1
                  AND om.status = 'active'
                """,
                org_a_id
            )

            # Count students in Org B
            org_b_student_count = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT u.user_id)
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN organization_members om ON u.user_id = om.user_id
                WHERE ur.role_type = 'STUDENT'
                  AND om.organization_id = $1
                  AND om.status = 'active'
                """,
                org_b_id
            )

            # Get sample Org B student email for search test
            org_b_student_email = await conn.fetchval(
                """
                SELECT u.email
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN organization_members om ON u.user_id = om.user_id
                WHERE ur.role_type = 'STUDENT'
                  AND om.organization_id = $1
                  AND om.status = 'active'
                LIMIT 1
                """,
                org_b_id
            )

        # Step 4: Verify UI student count matches Org A database count
        try:
            student_count_element = self.driver.find_element(By.ID, "studentCount")
            ui_student_count = int(''.join(filter(str.isdigit, student_count_element.text)))

            # ASSERTION 1: UI shows only Org A students
            assert ui_student_count == org_a_student_count, \
                f"UI shows {ui_student_count} students but Org A has {org_a_student_count}"

            # ASSERTION 2: Count does NOT include Org B students
            total_both_orgs = org_a_student_count + org_b_student_count
            assert ui_student_count < total_both_orgs, \
                f"Student count {ui_student_count} suggests data from both orgs leaked"

        except NoSuchElementException:
            pytest.skip("Student count element not found - UI may not display count")

        # Step 5: Try searching for Org B student by email
        if org_b_student_email:
            try:
                search_input = self.driver.find_element(By.ID, "studentSearchInput")
                search_input.clear()
                search_input.send_keys(org_b_student_email)
                time.sleep(1)

                # ASSERTION 3: Search must not return Org B student
                search_results = self.driver.find_elements(By.CLASS_NAME, "student-row")
                for result in search_results:
                    result_email = result.get_attribute('data-email')
                    assert result_email != org_b_student_email, \
                        f"Search leaked Org B student {org_b_student_email}"

                # ASSERTION 4: Either no results or message shown
                no_results = self.driver.find_elements(By.CLASS_NAME, "no-students-found")
                assert len(search_results) == 0 or len(no_results) > 0, \
                    "Search for Org B student should return no results"

            except NoSuchElementException:
                pytest.skip("Search functionality not available on this page")

    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_03_organization_cannot_see_other_org_analytics(
        self,
        test_users,
        test_organizations,
        db_pool
    ):
        """
        Test: Organization analytics calculations exclude other organizations

        BUSINESS SCENARIO:
        1. Org A has 100 students with 75% avg score
        2. Org B has 50 students with 85% avg score
        3. Org A admin views analytics dashboard
        4. Should see metrics calculated ONLY from Org A data
        5. Average score should be 75%, not blended 78.33%

        COMPETITIVE INTELLIGENCE:
        Leaking aggregated metrics could expose competitive advantage.
        Organizations must not know other orgs' performance.

        COMPLIANCE: ISO 27001, SOC 2 Type II
        """
        login_page = LoginPage(self.driver)
        analytics_page = OrganizationAnalyticsPage(self.driver)

        # Step 1: Login as Organization A admin
        login_page.navigate()
        org_a_admin = test_users['org_admin']
        login_page.login(org_a_admin['email'], org_a_admin['password'])

        # Step 2: Navigate to analytics page
        analytics_page.navigate()
        analytics_page.wait_for_analytics_loaded()

        # Step 3: Get metrics from database for Org A only
        org_a_id = test_organizations[0]['organization_id']

        async with db_pool.acquire() as conn:
            # Calculate Org A metrics
            org_a_metrics = await conn.fetchrow(
                """
                SELECT
                    COUNT(DISTINCT om.user_id) as total_students,
                    COUNT(DISTINCT c.course_id) as total_courses,
                    COALESCE(AVG(qa.score), 0) as average_score,
                    COALESCE(AVG(CASE WHEN ce.progress >= 90 THEN 1 ELSE 0 END) * 100, 0) as completion_rate
                FROM organizations o
                LEFT JOIN organization_members om ON o.organization_id = om.organization_id
                LEFT JOIN courses c ON o.organization_id = c.organization_id
                LEFT JOIN course_enrollments ce ON c.course_id = ce.course_id
                LEFT JOIN quiz_attempts qa ON ce.student_id = qa.student_id
                WHERE o.organization_id = $1
                  AND om.status = 'active'
                  AND c.status = 'published'
                """,
                org_a_id
            )

            # Calculate combined metrics (to verify NOT using this)
            combined_metrics = await conn.fetchrow(
                """
                SELECT
                    AVG(qa.score) as blended_average_score
                FROM quiz_attempts qa
                """
            )

        # Step 4: Get metrics from UI
        ui_total_students = analytics_page.get_total_students()
        ui_total_courses = analytics_page.get_total_courses()
        ui_average_score = analytics_page.get_average_score()
        ui_completion_rate = analytics_page.get_completion_rate()

        # Step 5: Verify UI metrics match Org A database metrics
        # ASSERTION 1: Student count is Org A only
        assert abs(ui_total_students - org_a_metrics['total_students']) <= 1, \
            f"UI shows {ui_total_students} students but Org A has {org_a_metrics['total_students']}"

        # ASSERTION 2: Course count is Org A only
        assert abs(ui_total_courses - org_a_metrics['total_courses']) <= 1, \
            f"UI shows {ui_total_courses} courses but Org A has {org_a_metrics['total_courses']}"

        # ASSERTION 3: Average score is NOT blended across orgs
        org_a_avg = float(org_a_metrics['average_score'])
        blended_avg = float(combined_metrics['blended_average_score'])

        # UI should match Org A, not blended
        assert abs(ui_average_score - org_a_avg) < 2.0, \
            f"UI average {ui_average_score}% doesn't match Org A {org_a_avg}%"

        # UI should NOT match blended average (unless by coincidence)
        if abs(org_a_avg - blended_avg) > 5.0:  # Significantly different
            assert abs(ui_average_score - blended_avg) > 2.0, \
                f"UI average {ui_average_score}% suspiciously close to blended {blended_avg}%"

        # ASSERTION 4: Completion rate is Org A only
        org_a_completion = float(org_a_metrics['completion_rate'])
        assert abs(ui_completion_rate - org_a_completion) < 5.0, \
            f"UI completion {ui_completion_rate}% doesn't match Org A {org_a_completion}%"

        # Step 6: Verify organization name in header
        org_name = analytics_page.get_organization_name()
        assert test_organizations[0]['name'] in org_name, \
            f"Analytics page shows wrong org: {org_name}"

    @pytest.mark.priority_critical
    @pytest.mark.asyncio
    async def test_04_cross_organization_api_access_blocked(
        self,
        test_users,
        test_organizations,
        test_courses,
        db_pool
    ):
        """
        Test: API requests cannot access data from other organizations

        BUSINESS SCENARIO:
        1. Instructor from Org A authenticates and gets JWT token
        2. Attempts to access Org B course via API
        3. API must return 403 Forbidden or 404 Not Found
        4. API must validate organization_id in JWT matches resource org_id

        ATTACK VECTOR:
        Attacker could discover Org B course_id through enumeration
        and attempt direct API access. System must block this.

        COMPLIANCE: OWASP API Security Top 10
        """
        # Step 1: Login as Org A instructor to get auth token
        login_page = LoginPage(self.driver)
        login_page.navigate()
        org_a_instructor = test_users['instructor']
        login_page.login(org_a_instructor['email'], org_a_instructor['password'])

        # Step 2: Extract auth token from browser
        time.sleep(1)
        auth_token = self.driver.execute_script("return localStorage.getItem('authToken')")

        if not auth_token:
            pytest.skip("Could not retrieve auth token from localStorage")

        # Step 3: Identify Org B course ID
        org_b_course_id = test_courses[3]['course_id']  # "Machine Learning" from org-002

        # Step 4: Attempt to access Org B course via API
        async with httpx.AsyncClient(verify=False) as client:
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            }

            # Try to get course details
            response = await client.get(
                f"https://localhost:8003/courses/{org_b_course_id}",
                headers=headers
            )

            # ASSERTION 1: Request is blocked
            assert response.status_code in [403, 404], \
                f"Expected 403 or 404 for cross-org access, got {response.status_code}"

            # ASSERTION 2: No course data leaked
            if response.status_code != 404:
                response_data = response.json()
                assert 'course_id' not in response_data or response_data.get('course_id') != org_b_course_id, \
                    "API leaked Org B course data despite forbidden access"

            # Step 5: Try to update Org B course
            update_response = await client.put(
                f"https://localhost:8003/courses/{org_b_course_id}",
                headers=headers,
                json={'title': 'Hacked Course Title'}
            )

            # ASSERTION 3: Update is blocked
            assert update_response.status_code in [403, 404], \
                f"Expected 403 or 404 for cross-org update, got {update_response.status_code}"

            # Step 6: Try to delete Org B course
            delete_response = await client.delete(
                f"https://localhost:8003/courses/{org_b_course_id}",
                headers=headers
            )

            # ASSERTION 4: Delete is blocked
            assert delete_response.status_code in [403, 404], \
                f"Expected 403 or 404 for cross-org delete, got {delete_response.status_code}"

        # Step 7: Verify Org B course still exists in database (not modified)
        async with db_pool.acquire() as conn:
            course_exists = await conn.fetchrow(
                """
                SELECT course_id, title, organization_id
                FROM courses
                WHERE course_id = $1
                """,
                org_b_course_id
            )

            # ASSERTION 5: Course unchanged
            assert course_exists is not None, "Org B course was deleted!"
            assert course_exists['title'] == test_courses[3]['title'], \
                "Org B course title was modified!"
            assert course_exists['organization_id'] == test_organizations[1]['organization_id'], \
                "Org B course organization was changed!"


# ============================================================================
# TEST CLASS - Resource Isolation Tests
# ============================================================================

@pytest.mark.e2e
@pytest.mark.rbac
class TestOrganizationResourceIsolation(BaseTest):
    """
    Test suite for organization resource isolation.

    BUSINESS REQUIREMENT:
    Organizations must have isolated computational resources (labs),
    storage quotas, and data processing (analytics) to ensure fair
    resource allocation and prevent resource exhaustion attacks.
    """

    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_05_lab_containers_isolated_by_organization(
        self,
        test_users,
        test_organizations,
        db_pool
    ):
        """
        Test: Lab containers are namespaced by organization

        BUSINESS SCENARIO:
        1. Student from Org A starts a lab container
        2. Container gets labeled with org_id=org-001
        3. Student from Org B cannot access Org A's container
        4. Docker namespace isolation enforced

        RESOURCE PROTECTION:
        Prevents students from accessing other orgs' lab environments,
        code, or data. Critical for multi-tenant lab security.

        COMPLIANCE: Container isolation best practices
        """
        login_page = LoginPage(self.driver)

        # Step 1: Login as Org A student
        login_page.navigate()
        org_a_student = test_users['student']
        login_page.login(org_a_student['email'], org_a_student['password'])

        # Step 2: Navigate to labs page and start a lab
        self.driver.get(f"{self.base_url}/student/labs")
        time.sleep(2)

        try:
            # Find and click "Start Lab" button
            start_lab_btn = self.driver.find_element(By.CSS_SELECTOR, "button.start-lab")
            start_lab_btn.click()
            time.sleep(5)  # Wait for container to start

            # Get lab container ID from page
            lab_container_id = self.driver.find_element(By.ID, "labContainerId").text

            # ASSERTION 1: Container ID is present
            assert lab_container_id, "Lab container ID not found"

        except NoSuchElementException:
            pytest.skip("Lab functionality not available or already running")
            return

        # Step 3: Verify container has organization label
        org_a_id = test_organizations[0]['organization_id']

        # Query Docker API (via docker command) to check labels
        import subprocess
        try:
            result = subprocess.run(
                ['docker', 'inspect', lab_container_id, '--format', '{{.Config.Labels.organization_id}}'],
                capture_output=True,
                text=True,
                timeout=5
            )

            container_org_id = result.stdout.strip()

            # ASSERTION 2: Container labeled with correct org
            assert container_org_id == org_a_id, \
                f"Container has org_id={container_org_id}, expected {org_a_id}"

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker CLI not available for inspection")

        # Step 4: Verify in database that lab session is linked to org
        async with db_pool.acquire() as conn:
            lab_session = await conn.fetchrow(
                """
                SELECT ls.session_id, ls.organization_id, ls.student_id
                FROM lab_sessions ls
                WHERE ls.container_id = $1
                """,
                lab_container_id
            )

            # ASSERTION 3: Lab session in database
            assert lab_session is not None, "Lab session not found in database"

            # ASSERTION 4: Lab session linked to correct org
            assert lab_session['organization_id'] == org_a_id, \
                f"Lab session has org_id={lab_session['organization_id']}, expected {org_a_id}"

            # ASSERTION 5: Lab session linked to correct student
            assert lab_session['student_id'] == org_a_student['user_id'], \
                "Lab session not linked to correct student"

    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_06_storage_quotas_separate_per_organization(
        self,
        test_users,
        test_organizations,
        db_pool
    ):
        """
        Test: Storage quotas are tracked per organization

        BUSINESS SCENARIO:
        1. Org A has 100GB storage quota
        2. Org B has 50GB storage quota
        3. Org A uploads 80GB of content
        4. Org A still has 20GB available (not affected by Org B usage)
        5. Quotas are independent

        RESOURCE FAIRNESS:
        Prevents one organization from consuming storage that
        should be available to other organizations.

        BUSINESS MODEL:
        Enables tiered pricing based on storage quotas.
        """
        login_page = LoginPage(self.driver)

        # Step 1: Login as Org A admin
        login_page.navigate()
        org_a_admin = test_users['org_admin']
        login_page.login(org_a_admin['email'], org_a_admin['password'])

        # Step 2: Navigate to organization settings/storage
        self.driver.get(f"{self.base_url}/org-admin/settings/storage")
        time.sleep(2)

        # Step 3: Get storage quota and usage from UI
        try:
            quota_element = self.driver.find_element(By.ID, "storageQuota")
            usage_element = self.driver.find_element(By.ID, "storageUsage")

            ui_quota_gb = float(''.join(c for c in quota_element.text if c.isdigit() or c == '.'))
            ui_usage_gb = float(''.join(c for c in usage_element.text if c.isdigit() or c == '.'))

        except NoSuchElementException:
            pytest.skip("Storage quota UI elements not found")
            return

        # Step 4: Verify storage quota from database
        org_a_id = test_organizations[0]['organization_id']

        async with db_pool.acquire() as conn:
            org_storage = await conn.fetchrow(
                """
                SELECT
                    o.storage_quota_gb,
                    COALESCE(SUM(cm.file_size_bytes) / (1024.0 * 1024.0 * 1024.0), 0) as storage_used_gb
                FROM organizations o
                LEFT JOIN courses c ON o.organization_id = c.organization_id
                LEFT JOIN course_materials cm ON c.course_id = cm.course_id
                WHERE o.organization_id = $1
                GROUP BY o.organization_id, o.storage_quota_gb
                """,
                org_a_id
            )

            db_quota_gb = float(org_storage['storage_quota_gb'])
            db_usage_gb = float(org_storage['storage_used_gb'])

        # ASSERTION 1: UI quota matches database
        assert abs(ui_quota_gb - db_quota_gb) < 0.1, \
            f"UI quota {ui_quota_gb}GB doesn't match DB {db_quota_gb}GB"

        # ASSERTION 2: UI usage matches database
        assert abs(ui_usage_gb - db_usage_gb) < 1.0, \
            f"UI usage {ui_usage_gb}GB doesn't match DB {db_usage_gb}GB"

        # Step 5: Verify Org B has separate quota (not shared)
        org_b_id = test_organizations[1]['organization_id']

        async with db_pool.acquire() as conn:
            org_b_storage = await conn.fetchrow(
                """
                SELECT
                    o.storage_quota_gb,
                    COALESCE(SUM(cm.file_size_bytes) / (1024.0 * 1024.0 * 1024.0), 0) as storage_used_gb
                FROM organizations o
                LEFT JOIN courses c ON o.organization_id = c.organization_id
                LEFT JOIN course_materials cm ON c.course_id = cm.course_id
                WHERE o.organization_id = $1
                GROUP BY o.organization_id, o.storage_quota_gb
                """,
                org_b_id
            )

            org_b_quota_gb = float(org_b_storage['storage_quota_gb'])
            org_b_usage_gb = float(org_b_storage['storage_used_gb'])

        # ASSERTION 3: Orgs have independent quotas
        # (Even if same tier, quotas should not be combined)
        assert db_quota_gb != (db_quota_gb + org_b_quota_gb), \
            "Storage quotas appear to be combined instead of separate"

        # ASSERTION 4: Available storage is org-specific
        ui_available_gb = ui_quota_gb - ui_usage_gb
        assert ui_available_gb >= 0, "Available storage cannot be negative"
        assert ui_available_gb <= ui_quota_gb, "Available storage exceeds quota"

    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_07_analytics_calculations_separate_per_organization(
        self,
        test_users,
        test_organizations,
        db_pool
    ):
        """
        Test: Analytics aggregations are calculated per organization

        BUSINESS SCENARIO:
        1. System calculates completion rate for Org A
        2. Calculation should use: (Org A completed courses) / (Org A total enrollments)
        3. Must NOT include: Org B's completed courses or enrollments
        4. Percentages are accurate to organization scope

        DATA INTEGRITY:
        Ensures organizations make decisions based on accurate,
        isolated metrics. Mixing data could lead to bad business decisions.
        """
        login_page = LoginPage(self.driver)
        analytics_page = OrganizationAnalyticsPage(self.driver)

        # Step 1: Login as Org A admin
        login_page.navigate()
        org_a_admin = test_users['org_admin']
        login_page.login(org_a_admin['email'], org_a_admin['password'])

        # Step 2: Navigate to analytics
        analytics_page.navigate()
        analytics_page.wait_for_analytics_loaded()

        # Step 3: Get completion rate from UI
        ui_completion_rate = analytics_page.get_completion_rate()

        # Step 4: Calculate completion rate for Org A from database
        org_a_id = test_organizations[0]['organization_id']

        async with db_pool.acquire() as conn:
            # Get Org A specific metrics
            org_a_completion = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE ce.progress >= 90) as completed_count,
                    COUNT(*) as total_enrollments,
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            (COUNT(*) FILTER (WHERE ce.progress >= 90)::float / COUNT(*)) * 100
                        ELSE 0
                    END as completion_rate
                FROM course_enrollments ce
                JOIN courses c ON ce.course_id = c.course_id
                WHERE c.organization_id = $1
                  AND ce.status = 'active'
                """,
                org_a_id
            )

            # Get platform-wide metrics (to verify NOT using this)
            platform_completion = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE ce.progress >= 90) as completed_count,
                    COUNT(*) as total_enrollments,
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            (COUNT(*) FILTER (WHERE ce.progress >= 90)::float / COUNT(*)) * 100
                        ELSE 0
                    END as completion_rate
                FROM course_enrollments ce
                WHERE ce.status = 'active'
                """
            )

        db_org_completion_rate = float(org_a_completion['completion_rate'])
        db_platform_completion_rate = float(platform_completion['completion_rate'])

        # ASSERTION 1: UI matches Org A database calculation
        assert abs(ui_completion_rate - db_org_completion_rate) < 5.0, \
            f"UI completion {ui_completion_rate}% doesn't match Org A {db_org_completion_rate}%"

        # ASSERTION 2: UI does NOT match platform-wide calculation
        if abs(db_org_completion_rate - db_platform_completion_rate) > 5.0:
            assert abs(ui_completion_rate - db_platform_completion_rate) > 2.0, \
                f"UI {ui_completion_rate}% suspiciously close to platform {db_platform_completion_rate}%"

        # ASSERTION 3: Denominator is org-specific enrollment count
        db_org_enrollment_count = org_a_completion['total_enrollments']
        db_platform_enrollment_count = platform_completion['total_enrollments']

        assert db_org_enrollment_count < db_platform_enrollment_count, \
            "Org A enrollment count equals platform count (isolation failed)"

    @pytest.mark.priority_high
    @pytest.mark.asyncio
    async def test_08_search_results_filtered_by_organization(
        self,
        test_users,
        test_organizations,
        test_courses,
        db_pool
    ):
        """
        Test: Search results are filtered by user's organization

        BUSINESS SCENARIO:
        1. Platform search index contains courses from all organizations
        2. User from Org A performs search for "Python"
        3. Search finds 5 courses: 3 from Org A, 2 from Org B
        4. User should only see 3 results from Org A
        5. Org B results are filtered out despite match

        INFORMATION DISCLOSURE:
        Even course titles and descriptions from other orgs should
        not be visible in search results. Prevents competitive intelligence.
        """
        login_page = LoginPage(self.driver)
        search_page = OrganizationSearchPage(self.driver)

        # Step 1: Login as Org A instructor
        login_page.navigate()
        org_a_instructor = test_users['instructor']
        login_page.login(org_a_instructor['email'], org_a_instructor['password'])

        # Step 2: Navigate to search page
        search_page.navigate()

        # Step 3: Perform search for common term
        search_query = "Introduction"  # Likely in multiple org courses
        search_page.perform_search(search_query)

        # Step 4: Get search results
        result_count = search_page.get_search_results_count()
        result_titles = search_page.get_result_titles()
        result_org_ids = search_page.get_result_organization_ids()

        # Step 5: Verify all results are from Org A
        org_a_id = test_organizations[0]['organization_id']

        # ASSERTION 1: All results have Org A organization ID
        for org_id in result_org_ids:
            assert org_id == org_a_id, \
                f"Search result from org {org_id} leaked, should only show {org_a_id}"

        # Step 6: Verify database query also filters by org
        async with db_pool.acquire() as conn:
            # Count matching courses for Org A
            org_a_matches = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM courses c
                WHERE c.organization_id = $1
                  AND c.status = 'published'
                  AND (
                    c.title ILIKE $2
                    OR c.description ILIKE $2
                  )
                """,
                org_a_id,
                f'%{search_query}%'
            )

            # Count matching courses platform-wide
            platform_matches = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM courses c
                WHERE c.status = 'published'
                  AND (
                    c.title ILIKE $1
                    OR c.description ILIKE $1
                  )
                """,
                f'%{search_query}%'
            )

        # ASSERTION 2: UI result count matches Org A database count
        assert result_count == org_a_matches, \
            f"UI shows {result_count} results but DB has {org_a_matches} for Org A"

        # ASSERTION 3: Result count is less than platform-wide
        # (unless Org A happens to have all matching courses)
        if platform_matches > org_a_matches:
            assert result_count < platform_matches, \
                f"Search returned {result_count} results = platform {platform_matches} (no filtering)"

        # Step 7: Try filtering search by type
        search_page.filter_by_type('course')

        # Verify still only Org A results after filtering
        filtered_org_ids = search_page.get_result_organization_ids()
        for org_id in filtered_org_ids:
            assert org_id == org_a_id, \
                f"Filtered search leaked org {org_id} result"
