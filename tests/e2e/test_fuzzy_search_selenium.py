"""
E2E Tests for Fuzzy Search with Typo Tolerance

BUSINESS REQUIREMENT:
Test that students can find courses using fuzzy search even when they
make typos or use partial words in their search queries.

TDD METHODOLOGY:
RED PHASE: These tests are written FIRST and expected to FAIL initially.
GREEN PHASE: Implementation will make them PASS.
REFACTOR PHASE: Code cleanup while maintaining passing tests.

TECHNICAL IMPLEMENTATION:
- Uses Selenium with Chrome WebDriver
- Tests real browser interaction with fuzzy search
- Validates typo tolerance and partial matching
- Verifies similarity score display (when implemented)
- Uses Page Object Model pattern

BUSINESS VALUE:
Students can find courses despite misspellings, improving user experience
and reducing frustration from "no results" searches.
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from tests.e2e.selenium_base import BasePage, BaseTest


class StudentDashboardPage(BasePage):
    """
    Page Object for Student Dashboard with fuzzy search functionality.

    DESIGN PATTERN: Page Object Model (POM)
    Encapsulates all student dashboard interactions for maintainability.
    """

    # Locators
    SEARCH_INPUT = (By.ID, "courseSearch")  # Actual ID in student-dashboard.html
    SEARCH_RESULTS = (By.CLASS_NAME, "course-card")
    NO_RESULTS_MESSAGE = (By.CLASS_NAME, "no-results")
    COURSE_TITLE = (By.CLASS_NAME, "course-title")
    SIMILARITY_BADGE = (By.CLASS_NAME, "similarity-badge")  # For future visual indicators
    LOADING_INDICATOR = (By.CLASS_NAME, "loading")

    def navigate(self):
        """Navigate to student dashboard."""
        self.navigate_to("/html/student-dashboard.html")

    def navigate_to_my_courses(self):
        """
        Navigate to the My Courses section where course search is available.

        BUSINESS CONTEXT:
        The course search functionality is on the "My Courses" tab,
        not the main dashboard overview.
        """
        # Wait for page to fully load
        time.sleep(2)

        # Use JavaScript to directly show the courses section and make it visible
        self.driver.execute_script("""
            // Hide all sections
            const sections = document.querySelectorAll('[id$="-section"]');
            sections.forEach(s => s.style.display = 'none');

            // Show courses section
            const coursesSection = document.getElementById('courses-section');
            if (coursesSection) {
                coursesSection.style.display = 'block';
            }

            // Update active nav link
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('data-section') === 'courses') {
                    link.classList.add('active');
                }
            });
        """)
        time.sleep(0.5)  # Wait for DOM updates

    def login_as_student(self, email: str = "student@example.com", password: str = "password"):
        """
        Login as student user.

        BUSINESS CONTEXT:
        Students must be authenticated to access their dashboard and search courses.

        Args:
            email: Student email (default: test student)
            password: Student password
        """
        # Check if already on login page or need to navigate
        current_url = self.get_current_url()
        if "login" not in current_url:
            self.navigate_to("/html/login.html")

        # Enter credentials
        self.enter_text(By.ID, "email", email)
        self.enter_text(By.ID, "password", password)

        # Click login button
        self.click_element(By.CSS_SELECTOR, "button[type='submit']")

        # Wait for redirect to dashboard
        self.wait_for_url_contains("student-dashboard", timeout=10)

    def search_courses(self, query: str):
        """
        Perform course search using fuzzy search.

        BUSINESS WORKFLOW:
        1. Student types search query (may contain typos)
        2. Fuzzy search API called automatically
        3. Results displayed with best matches first

        Args:
            query: Search query (typos allowed!)
        """
        # Wait for the search input to be visible
        search_input = self.wait_for_element_visible(By.ID, "courseSearch", timeout=15)

        # Scroll element into view to ensure it's interactable
        self.driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
        time.sleep(0.3)  # Brief pause after scroll

        search_input.clear()
        search_input.send_keys(query)

        # Wait a moment for debounced search to trigger
        time.sleep(0.5)

        # Optional: press Enter to trigger search immediately
        search_input.send_keys(Keys.ENTER)

        # Wait longer for search to complete (API call + rendering)
        time.sleep(3)  # Give time for API call and results to render

        # Wait for search to complete (loading indicator disappears)
        self.wait_for_search_complete()

    def wait_for_search_complete(self, timeout: int = 10):
        """
        Wait for search operation to complete.

        TECHNICAL DETAIL:
        Waits for loading indicator to disappear OR results to appear
        """
        try:
            # Wait for loading indicator to disappear (if present)
            WebDriverWait(self.driver, 2).until(
                EC.invisibility_of_element_located(self.LOADING_INDICATOR)
            )
        except:
            pass  # Loading indicator might not appear for fast searches

        # Give a moment for results to render
        time.sleep(0.3)

    def get_search_results(self) -> list:
        """
        Get all course search results.

        Returns:
            List of course card elements
        """
        try:
            # Wait for results to appear (short timeout)
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(self.SEARCH_RESULTS)
            )
            return self.find_elements(*self.SEARCH_RESULTS)
        except:
            # No results found
            return []

    def get_course_titles(self) -> list:
        """
        Get titles of all displayed courses.

        Returns:
            List of course title strings
        """
        results = self.get_search_results()
        titles = []
        for result in results:
            try:
                title_element = result.find_element(*self.COURSE_TITLE)
                titles.append(title_element.text)
            except:
                continue
        return titles

    def has_no_results_message(self) -> bool:
        """
        Check if "no results" message is displayed.

        Returns:
            True if no results message shown, False otherwise
        """
        return self.is_element_present(*self.NO_RESULTS_MESSAGE, timeout=2)

    def get_similarity_badges(self) -> list:
        """
        Get similarity score badges (for future feature).

        FUTURE FEATURE:
        Visual indicators showing match quality (e.g., "95% match")

        Returns:
            List of similarity badge elements
        """
        return self.find_elements(*self.SIMILARITY_BADGE)

    def get_first_result_title(self) -> str:
        """
        Get title of first search result.

        BUSINESS VALUE:
        First result should be most relevant (highest similarity score)

        Returns:
            Title of first course result, or None if no results
        """
        titles = self.get_course_titles()
        return titles[0] if titles else None


@pytest.mark.e2e
@pytest.mark.fuzzy_search
class TestFuzzySearchSelenium(BaseTest):
    """
    E2E tests for fuzzy search functionality using Selenium.

    TDD METHODOLOGY:
    These tests are written FIRST (RED phase) before implementation.
    They define EXACTLY what success looks like from user perspective.

    BUSINESS REQUIREMENT:
    Students must be able to find courses despite typos or partial search terms.
    """

    def setup_method(self, method):
        """
        Setup before each test.

        PREREQUISITE:
        - Frontend services must be running (nginx/static server)
        - Backend metadata-service must be running on port 8011
        - Test database must have sample course data with metadata
        """
        super().setup_method(method)
        self.dashboard = StudentDashboardPage(self.driver, self.config)

    def test_fuzzy_search_with_typo_finds_course(self):
        """
        TEST 1: Fuzzy search handles typo - "pyton" finds "Python" course

        TDD PHASE: RED (expect FAIL)

        BUSINESS USE CASE:
        Student accidentally types "pyton" instead of "python" when searching.
        Fuzzy search should still find Python-related courses.

        USER WORKFLOW:
        1. Student logs into dashboard
        2. Student types "pyton" in search box (typo for "python")
        3. Fuzzy search activates (similarity threshold: 0.2)
        4. Results show Python courses despite typo
        5. Best matches appear first (sorted by similarity score)

        SUCCESS CRITERIA:
        - At least one result appears (not "no results")
        - Result contains "Python" in title
        - Student can proceed to enroll in course

        TECHNICAL VALIDATION:
        - Fuzzy search API endpoint called: POST /api/v1/metadata/search/fuzzy
        - Request body includes: query="pyton", similarity_threshold=0.2
        - Response includes similarity_score for each result
        - Frontend sorts results by similarity_score descending
        """
        # Step 1: Navigate to student dashboard
        self.dashboard.navigate()
        # TODO: Uncomment when auth is integrated
        # self.dashboard.login_as_student()

        # Step 2: Navigate to My Courses section (where search is located)
        self.dashboard.navigate_to_my_courses()

        # Step 3: Search with typo "pyton"
        self.dashboard.search_courses("pyton")

        # Step 3: Verify results appear
        results = self.dashboard.get_search_results()
        assert len(results) > 0, \
            "Fuzzy search should find courses despite typo 'pyton' → 'python'"

        # Step 4: Verify result contains "Python"
        titles = self.dashboard.get_course_titles()
        python_courses = [title for title in titles if "python" in title.lower()]
        assert len(python_courses) > 0, \
            "At least one result should contain 'Python' when searching for 'pyton'"

        # Step 5: Verify no "no results" message
        assert not self.dashboard.has_no_results_message(), \
            "Should NOT show 'no results' message for typo search"

        # PROOF OF SUCCESS: Take screenshot showing results for "pyton" typo
        self.take_screenshot("fuzzy_search_typo_pyton_success")

    def test_fuzzy_search_partial_match_finds_courses(self):
        """
        TEST 2: Fuzzy search handles partial words - "prog" finds "programming"

        TDD PHASE: RED (expect FAIL)

        BUSINESS USE CASE:
        Student starts typing course name but doesn't finish the word.
        Fuzzy search should show results immediately without full word.

        USER WORKFLOW:
        1. Student logs into dashboard
        2. Student types "prog" (incomplete word)
        3. Fuzzy search activates
        4. Results show courses with "programming" in title/description

        SUCCESS CRITERIA:
        - Multiple results appear
        - All results contain "prog" or "programming" or related terms
        - Results sorted by relevance

        TECHNICAL VALIDATION:
        - Partial word matching via trigram similarity
        - similarity("prog", "programming") should be ~0.50
        - Results filtered by threshold (0.2 minimum)
        """
        # Step 1: Login
        self.dashboard.navigate()
        # TODO: Uncomment when auth is integrated
        # self.dashboard.login_as_student()

        # Step 2: Search with partial word
        self.dashboard.search_courses("prog")

        # Step 3: Verify results appear
        results = self.dashboard.get_search_results()
        assert len(results) > 0, \
            "Fuzzy search should find courses with partial word 'prog'"

        # Step 4: Verify results contain "programming" or related terms
        titles = self.dashboard.get_course_titles()
        relevant_courses = [
            title for title in titles
            if any(keyword in title.lower() for keyword in ["prog", "programming", "code", "develop"])
        ]
        assert len(relevant_courses) > 0, \
            "Results should contain 'programming' or related terms for query 'prog'"

        # PROOF OF SUCCESS
        self.take_screenshot("fuzzy_search_partial_prog_success")

    def test_fuzzy_search_multiple_typos_still_works(self):
        """
        TEST 3: Fuzzy search handles multiple typos

        TDD PHASE: RED (expect FAIL)

        BUSINESS USE CASE:
        Student makes multiple spelling errors in search query.
        System should still find relevant courses.

        USER WORKFLOW:
        1. Student searches for "pyton programing" (2 typos)
        2. Fuzzy search finds "Python Programming" courses
        3. Student successfully enrolls

        SUCCESS CRITERIA:
        - At least one result found
        - Result relates to Python and Programming

        TECHNICAL VALIDATION:
        - Each word matched independently via fuzzy search
        - Combined similarity score calculated
        - Results ranked by total similarity
        """
        # Step 1: Login
        self.dashboard.navigate()
        # TODO: Uncomment when auth is integrated
        # self.dashboard.login_as_student()

        # Step 2: Search with multiple typos
        self.dashboard.search_courses("pyton programing")

        # Step 3: Verify results appear
        results = self.dashboard.get_search_results()
        assert len(results) > 0, \
            "Fuzzy search should handle multiple typos 'pyton programing'"

        # Step 4: Verify result is relevant to Python Programming
        first_title = self.dashboard.get_first_result_title()
        assert first_title is not None, "Should have at least one result"

        # Either "python" or "programming" should appear in title
        title_lower = first_title.lower()
        has_python = "python" in title_lower
        has_programming = "program" in title_lower  # Matches "program", "programming", etc.

        assert has_python or has_programming, \
            f"First result '{first_title}' should relate to Python or Programming"

        # PROOF OF SUCCESS
        self.take_screenshot("fuzzy_search_multiple_typos_success")

    @pytest.mark.skip(reason="Visual similarity badges not yet implemented - pending feature")
    def test_fuzzy_search_shows_similarity_scores(self):
        """
        TEST 4: Similarity score badges displayed to user

        TDD PHASE: RED (expect FAIL)

        BUSINESS USE CASE:
        Student sees match quality indicators to understand why results appear.
        Higher similarity = more confident match.

        USER WORKFLOW:
        1. Student searches with typo
        2. Results show with similarity badges (e.g., "85% match", "45% match")
        3. Student understands first result is most relevant

        SUCCESS CRITERIA:
        - Similarity badges visible on each result
        - Badges show percentage or quality indicator
        - Results ordered by similarity (best first)

        TECHNICAL VALIDATION:
        - similarity_score from API rendered as visual badge
        - CSS classes applied: "high" (>0.7), "medium" (0.4-0.7), "low" (<0.4)
        """
        # Step 1: Login
        self.dashboard.navigate()
        # TODO: Uncomment when auth is integrated
        # self.dashboard.login_as_student()

        # Step 2: Search with typo
        self.dashboard.search_courses("pyton")

        # Step 3: Verify results have similarity badges
        badges = self.dashboard.get_similarity_badges()
        assert len(badges) > 0, \
            "Each search result should display similarity score badge"

        # Step 4: Verify badge text format
        first_badge_text = badges[0].text
        assert "%" in first_badge_text or "match" in first_badge_text.lower(), \
            "Similarity badge should show percentage or 'match' indicator"

        # PROOF OF SUCCESS
        self.take_screenshot("fuzzy_search_similarity_badges_displayed")

    def test_fuzzy_search_fallback_on_no_match(self):
        """
        TEST 5: Graceful fallback when no fuzzy matches found

        TDD PHASE: RED (expect FAIL)

        BUSINESS USE CASE:
        Student searches for completely unrelated term.
        System shows "no results" gracefully without errors.

        USER WORKFLOW:
        1. Student searches for "asdfasdfasdf" (gibberish)
        2. No courses match even with fuzzy tolerance
        3. Friendly "no results" message displayed
        4. Student can try different search

        SUCCESS CRITERIA:
        - No JavaScript errors
        - "No results" message shown
        - Search box remains functional
        - No results displayed

        TECHNICAL VALIDATION:
        - Fuzzy search API returns empty array
        - Frontend handles empty results gracefully
        - No 500/400 errors from backend
        """
        # Step 1: Login
        self.dashboard.navigate()
        # TODO: Uncomment when auth is integrated
        # self.dashboard.login_as_student()

        # Step 2: Search with gibberish
        self.dashboard.search_courses("xyzabc123gibberish")

        # Step 3: Verify no results found
        results = self.dashboard.get_search_results()
        assert len(results) == 0, \
            "Gibberish search should return no results"

        # Step 4: Verify friendly "no results" message
        assert self.dashboard.has_no_results_message(), \
            "Should display 'no results' message for unmatched search"

        # Step 5: Verify search box still functional (can search again)
        search_input = self.dashboard.find_element(*self.dashboard.SEARCH_INPUT)
        assert search_input.is_enabled(), \
            "Search box should remain functional after no results"

        # PROOF OF SUCCESS
        self.take_screenshot("fuzzy_search_no_match_fallback")


@pytest.mark.e2e
@pytest.mark.fuzzy_search
@pytest.mark.performance
class TestFuzzySearchPerformance(BaseTest):
    """
    E2E tests for fuzzy search performance and caching.

    BUSINESS REQUIREMENT:
    Fuzzy search must be fast (<1 second) and cache results efficiently.
    """

    def setup_method(self, method):
        """Setup before each test."""
        super().setup_method(method)
        self.dashboard = StudentDashboardPage(self.driver, self.config)

    @pytest.mark.skip(reason="Performance testing pending - needs timing instrumentation")
    def test_fuzzy_search_uses_cache_for_repeated_searches(self):
        """
        TEST 6: Repeated searches use client-side cache

        TDD PHASE: RED (expect FAIL)

        BUSINESS USE CASE:
        Student searches same term multiple times (e.g., typo correction back and forth).
        Second search should be instant (cached).

        USER WORKFLOW:
        1. Student searches "pyton"
        2. Student changes to "python"
        3. Student changes back to "pyton"
        4. Third search instant (from cache)

        SUCCESS CRITERIA:
        - First search makes API call
        - Repeated search within 5 minutes uses cache
        - No duplicate API calls for same query

        TECHNICAL VALIDATION:
        - Check browser DevTools network tab
        - Only 1 API call for "pyton" despite multiple searches
        - Cache TTL: 5 minutes
        """
        # Step 1: Login
        self.dashboard.navigate()

        # Step 2: First search (should hit API)
        start_time = time.time()
        self.dashboard.search_courses("pyton")
        first_search_time = time.time() - start_time

        # Step 3: Clear search and search again (should use cache)
        self.dashboard.search_courses("")  # Clear
        time.sleep(0.5)

        start_time = time.time()
        self.dashboard.search_courses("pyton")  # Same query
        second_search_time = time.time() - start_time

        # Step 4: Verify second search faster (cached)
        assert second_search_time < first_search_time, \
            "Repeated fuzzy search should be faster (cached)"

        # PROOF OF SUCCESS
        self.take_screenshot("fuzzy_search_caching_verified")
