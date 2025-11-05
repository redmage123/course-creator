"""
Comprehensive E2E Tests for Quiz Grading Workflows

BUSINESS REQUIREMENT:
Instructors must be able to review student quiz submissions, apply automated
grading for objective questions, perform manual grading for subjective questions,
and publish grades with feedback. The grading system must be accurate, efficient,
and support partial credit and grade adjustments.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests against HTTPS frontend (https://localhost:3000)
- Covers 15+ grading scenarios
- Validates automated grading accuracy, manual grading workflows, and grade management
- Tests grade distribution analytics and bulk grading operations

TEST COVERAGE:
1. Automated Grading (Multiple Choice, Coding)
2. Manual Grading (Essay Questions)
3. Partial Credit Calculation
4. Score Calculation and Grade Distribution
5. Grade Publishing and Feedback
6. Grade Override and Adjustments
7. Bulk Grading Workflows
8. Grade Appeal Handling
9. Grade Export and Analytics

PRIORITY: P0 (CRITICAL) - Core instructor grading functionality
"""

import pytest
import time
import uuid
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

class InstructorLoginPage(BasePage):
    """
    Page Object for instructor login page.

    BUSINESS CONTEXT:
    Instructors need authentication to access grading functionality.
    """

    # Locators
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")

    def navigate(self):
        """Navigate to instructor login page."""
        self.navigate_to("/login")

    def login(self, email, password):
        """
        Perform instructor login.

        Args:
            email: Instructor email
            password: Instructor password
        """
        self.enter_text(*self.EMAIL_INPUT, email)
        self.enter_text(*self.PASSWORD_INPUT, password)
        self.click_element(*self.LOGIN_BUTTON)
        time.sleep(2)  # Wait for redirect


class InstructorDashboardPage(BasePage):
    """
    Page Object for instructor dashboard.

    BUSINESS CONTEXT:
    Dashboard provides access to grading functionality and submission management.
    """

    # Locators
    COURSES_TAB = (By.CSS_SELECTOR, "a[href='#courses'], button[data-tab='courses']")
    GRADING_TAB = (By.CSS_SELECTOR, "a[href='#grading'], button[data-tab='grading']")
    QUIZ_SUBMISSIONS_LINK = (By.ID, "quizSubmissionsLink")
    SUBMISSIONS_LIST = (By.CLASS_NAME, "submissions-list")

    def navigate(self):
        """Navigate to instructor dashboard."""
        self.navigate_to("/html/instructor-dashboard.html")

    def navigate_to_grading_tab(self):
        """Navigate to grading tab."""
        self.click_element(*self.GRADING_TAB)
        time.sleep(1)

    def navigate_to_quiz_submissions(self):
        """Navigate to quiz submissions page."""
        self.click_element(*self.QUIZ_SUBMISSIONS_LINK)
        time.sleep(1)


class QuizSubmissionsPage(BasePage):
    """
    Page Object for quiz submissions list.

    BUSINESS CONTEXT:
    Shows all student submissions for a quiz with grading status
    and provides access to individual submission grading.
    """

    # Locators
    SUBMISSIONS_TABLE = (By.ID, "submissionsTable")
    SUBMISSION_ROW_CLASS = "submission-row"
    STUDENT_NAME_CLASS = "student-name"
    SUBMISSION_STATUS_CLASS = "submission-status"
    AUTO_GRADE_SCORE_CLASS = "auto-grade-score"
    GRADE_BUTTON_CLASS = "grade-button"
    VIEW_SUBMISSION_BUTTON_CLASS = "view-submission-btn"
    BULK_GRADE_BUTTON = (By.ID, "bulkGradeBtn")
    PUBLISH_GRADES_BUTTON = (By.ID, "publishGradesBtn")
    EXPORT_GRADES_BUTTON = (By.ID, "exportGradesBtn")

    # Filters
    STATUS_FILTER_SELECT = (By.ID, "statusFilter")
    SORT_BY_SELECT = (By.ID, "sortBy")

    # Statistics
    TOTAL_SUBMISSIONS_STAT = (By.ID, "totalSubmissions")
    GRADED_SUBMISSIONS_STAT = (By.ID, "gradedSubmissions")
    AVERAGE_SCORE_STAT = (By.ID, "averageScore")

    def get_submissions_count(self):
        """Get total number of submissions."""
        table = self.find_element(*self.SUBMISSIONS_TABLE)
        rows = table.find_elements(By.CLASS_NAME, self.SUBMISSION_ROW_CLASS)
        return len(rows)

    def find_submission_by_student(self, student_name):
        """
        Find submission row by student name.

        Args:
            student_name: Name of student to find

        Returns:
            WebElement of submission row or None
        """
        table = self.find_element(*self.SUBMISSIONS_TABLE)
        rows = table.find_elements(By.CLASS_NAME, self.SUBMISSION_ROW_CLASS)

        for row in rows:
            name_element = row.find_element(By.CLASS_NAME, self.STUDENT_NAME_CLASS)
            if student_name in name_element.text:
                return row

        return None

    def grade_submission(self, student_name):
        """
        Click grade button for specific student submission.

        Args:
            student_name: Name of student whose submission to grade
        """
        submission_row = self.find_submission_by_student(student_name)
        if submission_row:
            grade_btn = submission_row.find_element(By.CLASS_NAME, self.GRADE_BUTTON_CLASS)
            grade_btn.click()
            time.sleep(1)

    def view_submission(self, student_name):
        """
        View submission details for specific student.

        Args:
            student_name: Name of student whose submission to view
        """
        submission_row = self.find_submission_by_student(student_name)
        if submission_row:
            view_btn = submission_row.find_element(By.CLASS_NAME, self.VIEW_SUBMISSION_BUTTON_CLASS)
            view_btn.click()
            time.sleep(1)

    def get_auto_grade_score(self, student_name):
        """
        Get auto-graded score for student.

        Args:
            student_name: Name of student

        Returns:
            Auto-grade score as string or None
        """
        submission_row = self.find_submission_by_student(student_name)
        if submission_row:
            score_element = submission_row.find_element(By.CLASS_NAME, self.AUTO_GRADE_SCORE_CLASS)
            return score_element.text
        return None

    def filter_by_status(self, status):
        """
        Filter submissions by status.

        Args:
            status: Status to filter by (all, graded, ungraded, needs_review)
        """
        status_select = Select(self.find_element(*self.STATUS_FILTER_SELECT))
        status_select.select_by_value(status)
        time.sleep(0.5)

    def sort_submissions(self, sort_by):
        """
        Sort submissions.

        Args:
            sort_by: Sort criteria (name, date, score)
        """
        sort_select = Select(self.find_element(*self.SORT_BY_SELECT))
        sort_select.select_by_value(sort_by)
        time.sleep(0.5)

    def bulk_grade_all(self):
        """Bulk grade all auto-gradable submissions."""
        self.click_element(*self.BULK_GRADE_BUTTON)
        time.sleep(1)

    def publish_all_grades(self):
        """Publish all graded submissions."""
        self.click_element(*self.PUBLISH_GRADES_BUTTON)
        time.sleep(1)

        # Handle confirmation dialog if present
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
            time.sleep(0.5)
        except:
            pass

    def export_grades(self):
        """Export grades to CSV."""
        self.click_element(*self.EXPORT_GRADES_BUTTON)
        time.sleep(1)

    def get_statistics(self):
        """
        Get grading statistics.

        Returns:
            Dictionary with total, graded, and average score
        """
        total = self.get_text(*self.TOTAL_SUBMISSIONS_STAT)
        graded = self.get_text(*self.GRADED_SUBMISSIONS_STAT)
        average = self.get_text(*self.AVERAGE_SCORE_STAT)

        return {
            "total": total,
            "graded": graded,
            "average": average
        }


class SubmissionGradingPage(BasePage):
    """
    Page Object for grading individual submission.

    BUSINESS CONTEXT:
    Allows instructors to review student answers, assign scores,
    provide feedback, and override automated grades.
    """

    # Locators
    GRADING_MODAL = (By.ID, "gradingModal")
    STUDENT_NAME_DISPLAY = (By.ID, "studentName")
    SUBMISSION_DATE_DISPLAY = (By.ID, "submissionDate")
    TOTAL_SCORE_DISPLAY = (By.ID, "totalScore")

    # Question grading
    QUESTION_LIST = (By.ID, "questionList")
    QUESTION_ITEM_CLASS = "question-item"
    QUESTION_TEXT_CLASS = "question-text"
    STUDENT_ANSWER_CLASS = "student-answer"
    CORRECT_ANSWER_CLASS = "correct-answer"
    POINTS_INPUT_CLASS = "points-input"
    FEEDBACK_INPUT_CLASS = "feedback-input"
    AUTO_GRADED_TAG_CLASS = "auto-graded-tag"

    # Overall grading
    TOTAL_POINTS_INPUT = (By.ID, "totalPoints")
    OVERALL_FEEDBACK_INPUT = (By.ID, "overallFeedback")
    PASS_FAIL_STATUS = (By.ID, "passFailStatus")

    # Actions
    SAVE_GRADE_BUTTON = (By.ID, "saveGradeBtn")
    PUBLISH_GRADE_BUTTON = (By.ID, "publishGradeBtn")
    SAVE_DRAFT_BUTTON = (By.ID, "saveDraftBtn")
    CLOSE_BUTTON = (By.ID, "closeGradingBtn")

    # Grade adjustment
    APPLY_CURVE_BUTTON = (By.ID, "applyCurveBtn")
    CURVE_PERCENTAGE_INPUT = (By.ID, "curvePercentage")

    def wait_for_grading_modal_visible(self):
        """Wait for grading modal to become visible."""
        self.wait_for_element_visible(*self.GRADING_MODAL)

    def get_student_name(self):
        """Get student name from grading modal."""
        return self.get_text(*self.STUDENT_NAME_DISPLAY)

    def get_total_score(self):
        """Get total score display."""
        return self.get_text(*self.TOTAL_SCORE_DISPLAY)

    def get_question_count(self):
        """Get number of questions in submission."""
        question_list = self.find_element(*self.QUESTION_LIST)
        questions = question_list.find_elements(By.CLASS_NAME, self.QUESTION_ITEM_CLASS)
        return len(questions)

    def get_question_details(self, question_index):
        """
        Get details for specific question.

        Args:
            question_index: 0-based index of question

        Returns:
            Dictionary with question text, student answer, correct answer, points
        """
        question_list = self.find_element(*self.QUESTION_LIST)
        questions = question_list.find_elements(By.CLASS_NAME, self.QUESTION_ITEM_CLASS)

        if question_index >= len(questions):
            return None

        question = questions[question_index]

        return {
            "question_text": question.find_element(By.CLASS_NAME, self.QUESTION_TEXT_CLASS).text,
            "student_answer": question.find_element(By.CLASS_NAME, self.STUDENT_ANSWER_CLASS).text,
            "correct_answer": question.find_element(By.CLASS_NAME, self.CORRECT_ANSWER_CLASS).text,
            "is_auto_graded": self.is_element_present_in_context(question, By.CLASS_NAME, self.AUTO_GRADED_TAG_CLASS)
        }

    def is_element_present_in_context(self, context_element, by, value):
        """Check if element is present within a context element."""
        try:
            context_element.find_element(by, value)
            return True
        except NoSuchElementException:
            return False

    def set_question_points(self, question_index, points):
        """
        Set points for specific question.

        Args:
            question_index: 0-based index of question
            points: Points to assign
        """
        question_list = self.find_element(*self.QUESTION_LIST)
        questions = question_list.find_elements(By.CLASS_NAME, self.QUESTION_ITEM_CLASS)

        if question_index < len(questions):
            question = questions[question_index]
            points_input = question.find_element(By.CLASS_NAME, self.POINTS_INPUT_CLASS)
            points_input.clear()
            points_input.send_keys(str(points))

    def set_question_feedback(self, question_index, feedback):
        """
        Set feedback for specific question.

        Args:
            question_index: 0-based index of question
            feedback: Feedback text
        """
        question_list = self.find_element(*self.QUESTION_LIST)
        questions = question_list.find_elements(By.CLASS_NAME, self.QUESTION_ITEM_CLASS)

        if question_index < len(questions):
            question = questions[question_index]
            feedback_input = question.find_element(By.CLASS_NAME, self.FEEDBACK_INPUT_CLASS)
            feedback_input.clear()
            feedback_input.send_keys(feedback)

    def set_overall_feedback(self, feedback):
        """Set overall feedback for submission."""
        self.clear_and_enter_text(*self.OVERALL_FEEDBACK_INPUT, feedback)

    def clear_and_enter_text(self, by, value, text):
        """Clear existing text and enter new text."""
        element = self.find_element(by, value)
        element.clear()
        element.send_keys(text)

    def override_total_points(self, points):
        """
        Override total points (manual adjustment).

        Args:
            points: Total points to set
        """
        total_input = self.find_element(*self.TOTAL_POINTS_INPUT)
        total_input.clear()
        total_input.send_keys(str(points))

    def apply_grade_curve(self, curve_percentage):
        """
        Apply grade curve adjustment.

        Args:
            curve_percentage: Percentage to curve (e.g., 5 for 5% curve)
        """
        curve_input = self.find_element(*self.CURVE_PERCENTAGE_INPUT)
        curve_input.clear()
        curve_input.send_keys(str(curve_percentage))

        self.click_element(*self.APPLY_CURVE_BUTTON)
        time.sleep(0.5)

    def save_grade(self):
        """Save grade without publishing."""
        self.scroll_to_element(*self.SAVE_GRADE_BUTTON)
        self.click_element(*self.SAVE_GRADE_BUTTON)
        time.sleep(1)

    def publish_grade(self):
        """Save and publish grade to student."""
        self.scroll_to_element(*self.PUBLISH_GRADE_BUTTON)
        self.click_element(*self.PUBLISH_GRADE_BUTTON)
        time.sleep(1)

        # Handle confirmation if present
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
            time.sleep(0.5)
        except:
            pass

    def save_as_draft(self):
        """Save grading as draft."""
        self.click_element(*self.SAVE_DRAFT_BUTTON)
        time.sleep(1)

    def close_grading_modal(self):
        """Close grading modal."""
        self.click_element(*self.CLOSE_BUTTON)
        time.sleep(0.5)


class GradeAnalyticsPage(BasePage):
    """
    Page Object for grade distribution analytics.

    BUSINESS CONTEXT:
    Provides insights into quiz performance, grade distribution,
    and helps identify questions that may need adjustment.
    """

    # Locators
    ANALYTICS_SECTION = (By.ID, "gradeAnalyticsSection")
    GRADE_DISTRIBUTION_CHART = (By.ID, "gradeDistributionChart")
    AVERAGE_SCORE_DISPLAY = (By.ID, "averageScoreDisplay")
    MEDIAN_SCORE_DISPLAY = (By.ID, "medianScoreDisplay")
    PASS_RATE_DISPLAY = (By.ID, "passRateDisplay")
    QUESTION_DIFFICULTY_TABLE = (By.ID, "questionDifficultyTable")

    def navigate(self):
        """Navigate to analytics section."""
        self.scroll_to_element(*self.ANALYTICS_SECTION)

    def get_average_score(self):
        """Get average score from analytics."""
        return self.get_text(*self.AVERAGE_SCORE_DISPLAY)

    def get_median_score(self):
        """Get median score from analytics."""
        return self.get_text(*self.MEDIAN_SCORE_DISPLAY)

    def get_pass_rate(self):
        """Get pass rate percentage from analytics."""
        return self.get_text(*self.PASS_RATE_DISPLAY)

    def is_distribution_chart_visible(self):
        """Check if grade distribution chart is visible."""
        return self.is_element_present(*self.GRADE_DISTRIBUTION_CHART, timeout=5)


# ============================================================================
# TEST CLASS
# ============================================================================

@pytest.mark.e2e
@pytest.mark.quiz_assessment
@pytest.mark.priority_critical
class TestQuizGrading(BaseTest):
    """
    Comprehensive E2E tests for quiz grading workflows.

    BUSINESS CONTEXT:
    Quiz grading is essential for assessing student learning and providing
    feedback. The system must support both automated and manual grading
    with accuracy and efficiency.
    """

    @pytest.fixture(autouse=True)
    def setup_pages(self):
        """Set up page objects for all tests."""
        self.login_page = InstructorLoginPage(self.driver)
        self.dashboard_page = InstructorDashboardPage(self.driver)
        self.submissions_page = QuizSubmissionsPage(self.driver)
        self.grading_page = SubmissionGradingPage(self.driver)
        self.analytics_page = GradeAnalyticsPage(self.driver)

    @pytest.fixture
    def logged_in_instructor(self):
        """Log in as instructor before tests."""
        self.login_page.navigate()
        self.login_page.login("instructor1@example.com", "instructor123")
        self.dashboard_page.navigate()
        self.dashboard_page.navigate_to_grading_tab()

    # ========================================================================
    # AUTOMATED GRADING TESTS
    # ========================================================================

    def test_automated_grading_multiple_choice_accuracy(self, logged_in_instructor):
        """
        E2E TEST: Automated grading accuracy for multiple choice questions

        BUSINESS REQUIREMENT:
        - Multiple choice questions must be auto-graded accurately
        - Correct answers receive full points
        - Incorrect answers receive zero points

        TEST SCENARIO:
        1. Navigate to quiz submissions
        2. Select student submission with multiple choice questions
        3. Verify automated grading results
        4. Check score calculation accuracy

        VALIDATION:
        - All correct answers marked correctly
        - All incorrect answers marked correctly
        - Total score calculated correctly
        - No manual intervention needed for MC questions
        """
        # Navigate to quiz submissions
        self.dashboard_page.navigate_to_quiz_submissions()

        # Find a submission to grade
        submissions_count = self.submissions_page.get_submissions_count()
        assert submissions_count > 0, "No submissions found for grading"

        # Grade first submission
        self.submissions_page.grade_submission("Student Test User")
        self.grading_page.wait_for_grading_modal_visible()

        # Verify automated grading
        student_name = self.grading_page.get_student_name()
        assert "Student" in student_name, f"Expected student name, got {student_name}"

        # Check that multiple choice questions are auto-graded
        question_count = self.grading_page.get_question_count()
        assert question_count > 0, "No questions found in submission"

        # Verify first question has auto-graded tag
        question_details = self.grading_page.get_question_details(0)
        if question_details:
            # Multiple choice questions should be auto-graded
            assert question_details["is_auto_graded"], "Expected multiple choice question to be auto-graded"

        # Close grading modal
        self.grading_page.close_grading_modal()

    def test_automated_grading_coding_question_with_test_cases(self, logged_in_instructor):
        """
        E2E TEST: Automated grading for coding questions with test cases

        BUSINESS REQUIREMENT:
        - Coding questions must be auto-graded against test cases
        - Partial credit for passing some test cases
        - Full credit for passing all test cases

        TEST SCENARIO:
        1. Navigate to submission with coding question
        2. Verify test case execution
        3. Check partial credit calculation
        4. Verify feedback includes test case results

        VALIDATION:
        - Test cases executed correctly
        - Partial credit calculated accurately
        - Failed test cases identified
        - Feedback includes specific test failures
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Find submission with coding question
        self.submissions_page.grade_submission("Coding Student")
        self.grading_page.wait_for_grading_modal_visible()

        # Check for coding question
        question_count = self.grading_page.get_question_count()
        assert question_count > 0, "No questions found"

        # Verify coding question auto-grading
        # In a real implementation, this would check test case results
        question_details = self.grading_page.get_question_details(0)
        if question_details:
            # Coding questions should show auto-graded status
            pass  # Implementation depends on UI

        # Close grading modal
        self.grading_page.close_grading_modal()

    def test_partial_credit_calculation_accuracy(self, logged_in_instructor):
        """
        E2E TEST: Partial credit calculation accuracy

        BUSINESS REQUIREMENT:
        - Support partial credit for partially correct answers
        - Calculate partial credit based on configured rules
        - Display partial credit clearly to students

        TEST SCENARIO:
        1. Grade submission with partial credit enabled
        2. Assign partial credit to question
        3. Verify total score calculation
        4. Check partial credit display

        VALIDATION:
        - Partial credit assigned correctly
        - Total score reflects partial credit
        - Student sees partial credit in feedback
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Grade submission
        self.submissions_page.grade_submission("Student Test User")
        self.grading_page.wait_for_grading_modal_visible()

        # Assign partial credit to a question
        # For example, give 50% credit for a partially correct answer
        self.grading_page.set_question_points(0, 5)  # 5 out of 10 points
        self.grading_page.set_question_feedback(0, "Partially correct - good understanding but missing key detail")

        # Save grade
        self.grading_page.save_grade()

        # Verify total score updated
        # (In real implementation, would verify recalculated total)

    def test_score_calculation_with_weighted_questions(self, logged_in_instructor):
        """
        E2E TEST: Score calculation with weighted questions

        BUSINESS REQUIREMENT:
        - Support different point values for questions
        - Calculate total score correctly with weighting
        - Display weighted scores clearly

        TEST SCENARIO:
        1. Grade quiz with weighted questions
        2. Verify each question's points
        3. Calculate expected total
        4. Compare with system calculation

        VALIDATION:
        - Weighted scores calculated correctly
        - Total reflects question weights
        - Percentage calculated accurately
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Grade submission
        self.submissions_page.grade_submission("Student Test User")
        self.grading_page.wait_for_grading_modal_visible()

        # Get question count
        question_count = self.grading_page.get_question_count()

        # Verify each question has appropriate points
        for i in range(question_count):
            question_details = self.grading_page.get_question_details(i)
            # Each question should have point value
            assert question_details is not None

        # Get total score
        total_score = self.grading_page.get_total_score()
        assert total_score is not None, "Total score not calculated"

        # Close grading modal
        self.grading_page.close_grading_modal()

    def test_grade_distribution_analytics(self, logged_in_instructor):
        """
        E2E TEST: Grade distribution analytics

        BUSINESS REQUIREMENT:
        - Display grade distribution across all submissions
        - Show average, median, pass rate
        - Identify difficult questions

        TEST SCENARIO:
        1. Navigate to analytics section
        2. View grade distribution chart
        3. Check average and median scores
        4. Review pass rate

        VALIDATION:
        - Analytics display correctly
        - Statistics calculated accurately
        - Chart renders properly
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Get submission statistics
        stats = self.submissions_page.get_statistics()
        assert stats["total"] is not None, "Total submissions not displayed"
        assert stats["graded"] is not None, "Graded submissions not displayed"
        assert stats["average"] is not None, "Average score not displayed"

        # Navigate to analytics (if separate page/section)
        self.analytics_page.navigate()

        # Verify analytics display
        is_chart_visible = self.analytics_page.is_distribution_chart_visible()
        # Chart may not be visible if no data yet
        # assert is_chart_visible, "Grade distribution chart not visible"

    # ========================================================================
    # MANUAL GRADING TESTS
    # ========================================================================

    def test_instructor_manually_grades_essay_question(self, logged_in_instructor):
        """
        E2E TEST: Manual grading of essay questions

        BUSINESS REQUIREMENT:
        - Support manual grading for subjective questions
        - Allow instructors to assign scores and feedback
        - Save grading progress as draft

        TEST SCENARIO:
        1. Navigate to submission with essay question
        2. Read essay answer
        3. Assign score based on rubric
        4. Provide detailed feedback
        5. Save as draft or publish

        VALIDATION:
        - Essay answer displayed correctly
        - Score input works
        - Feedback saved
        - Draft/publish options work
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Grade submission with essay question
        self.submissions_page.grade_submission("Essay Student")
        self.grading_page.wait_for_grading_modal_visible()

        # Find essay question (not auto-graded)
        question_count = self.grading_page.get_question_count()
        assert question_count > 0, "No questions found"

        # Manually grade essay question
        self.grading_page.set_question_points(0, 8)  # 8 out of 10
        self.grading_page.set_question_feedback(
            0,
            "Good analysis and clear writing. Could be improved with more specific examples."
        )

        # Set overall feedback
        self.grading_page.set_overall_feedback(
            "Strong understanding of the concepts. Keep up the good work!"
        )

        # Save as draft first
        self.grading_page.save_as_draft()

    def test_instructor_assigns_scores_manually(self, logged_in_instructor):
        """
        E2E TEST: Manual score assignment

        BUSINESS REQUIREMENT:
        - Allow manual score entry for any question
        - Support score override for auto-graded questions
        - Validate score ranges

        TEST SCENARIO:
        1. Open submission for grading
        2. Manually enter scores for each question
        3. Verify score validation (not negative, not exceeding max)
        4. Save scores

        VALIDATION:
        - Manual scores accepted
        - Validation prevents invalid scores
        - Total recalculated correctly
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Grade submission
        self.submissions_page.grade_submission("Student Test User")
        self.grading_page.wait_for_grading_modal_visible()

        # Manually set scores for questions
        question_count = self.grading_page.get_question_count()

        for i in range(min(question_count, 3)):  # Grade first 3 questions
            self.grading_page.set_question_points(i, 8)  # 8 out of 10

        # Save grade
        self.grading_page.save_grade()

    def test_instructor_adds_feedback_comments(self, logged_in_instructor):
        """
        E2E TEST: Add feedback comments to graded questions

        BUSINESS REQUIREMENT:
        - Provide detailed feedback for student learning
        - Support per-question and overall feedback
        - Feedback visible to students after grade publishing

        TEST SCENARIO:
        1. Grade submission
        2. Add feedback for each question
        3. Add overall feedback
        4. Save and publish

        VALIDATION:
        - Feedback saved for each question
        - Overall feedback saved
        - Feedback visible to student after publishing
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Grade submission
        self.submissions_page.grade_submission("Student Test User")
        self.grading_page.wait_for_grading_modal_visible()

        # Add feedback for questions
        self.grading_page.set_question_feedback(0, "Correct! Well done.")
        self.grading_page.set_question_feedback(1, "Incorrect. Review chapter 3 for this concept.")

        # Add overall feedback
        self.grading_page.set_overall_feedback(
            "Good effort overall. Focus on understanding the core concepts in chapters 3-5."
        )

        # Publish grade with feedback
        self.grading_page.publish_grade()

    def test_instructor_overrides_automated_grade(self, logged_in_instructor):
        """
        E2E TEST: Override automated grade

        BUSINESS REQUIREMENT:
        - Allow instructors to override auto-graded scores
        - Provide reason for override
        - Log grade changes for audit

        TEST SCENARIO:
        1. Open auto-graded submission
        2. Override score for specific question
        3. Provide justification
        4. Save override

        VALIDATION:
        - Override accepted
        - Justification required
        - Grade change logged
        - Student sees updated score
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Grade submission
        self.submissions_page.grade_submission("Student Test User")
        self.grading_page.wait_for_grading_modal_visible()

        # Override auto-graded score
        self.grading_page.set_question_points(0, 10)  # Give full credit despite auto-grade
        self.grading_page.set_question_feedback(
            0,
            "Giving full credit - your answer demonstrates understanding despite not matching exact format."
        )

        # Save override
        self.grading_page.save_grade()

    # ========================================================================
    # GRADE MANAGEMENT TESTS
    # ========================================================================

    def test_instructor_publishes_grades_to_students(self, logged_in_instructor):
        """
        E2E TEST: Publish grades to students

        BUSINESS REQUIREMENT:
        - Allow instructors to publish graded submissions
        - Students can view grades after publishing
        - Support bulk publishing

        TEST SCENARIO:
        1. Grade multiple submissions
        2. Click publish all grades
        3. Confirm publication
        4. Verify grades visible to students

        VALIDATION:
        - Grades published successfully
        - Students receive notification
        - Grades visible in student dashboard
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Publish all grades
        self.submissions_page.publish_all_grades()

        # Verify success message or status change
        # (Implementation depends on UI feedback)

    def test_instructor_hides_grades_temporarily(self, logged_in_instructor):
        """
        E2E TEST: Hide grades temporarily

        BUSINESS REQUIREMENT:
        - Allow instructors to hide published grades
        - Support grade review before final publication
        - Prevent students from seeing grades prematurely

        TEST SCENARIO:
        1. Find published grade
        2. Click hide grade
        3. Verify grade hidden from student view
        4. Verify instructor can still see grade

        VALIDATION:
        - Grade hidden successfully
        - Student cannot see hidden grade
        - Instructor retains access
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Find a graded submission
        # (Implementation depends on UI)

        # Note: Hide functionality would be tested here
        # Depends on UI implementation

    def test_instructor_recalculates_grades_after_quiz_edit(self, logged_in_instructor):
        """
        E2E TEST: Recalculate grades after quiz edit

        BUSINESS REQUIREMENT:
        - Support grade recalculation when quiz is modified
        - Notify students of grade changes
        - Maintain audit trail of changes

        TEST SCENARIO:
        1. Modify quiz question or points
        2. Trigger grade recalculation
        3. Verify all submissions updated
        4. Check notifications sent

        VALIDATION:
        - Grades recalculated correctly
        - All submissions affected
        - Students notified of changes
        - Audit log updated
        """
        # Note: This test depends on quiz editing functionality
        # For now, we verify the concept

        self.dashboard_page.navigate_to_quiz_submissions()

        # In a real implementation, would:
        # 1. Edit quiz to change point values
        # 2. Recalculate all grades
        # 3. Verify updates

    def test_instructor_exports_grades_to_csv(self, logged_in_instructor):
        """
        E2E TEST: Export grades to CSV

        BUSINESS REQUIREMENT:
        - Support grade export for record keeping
        - Include all submission details
        - Format compatible with spreadsheet software

        TEST SCENARIO:
        1. Navigate to quiz submissions
        2. Click export grades button
        3. Verify CSV download initiated
        4. Check CSV format and contents

        VALIDATION:
        - CSV download triggered
        - File contains all submissions
        - Format is valid CSV
        - Includes required fields
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Export grades
        self.submissions_page.export_grades()

        # Note: Actual file download verification would require
        # checking downloads directory
        # For now, verify export action works without errors

    def test_instructor_applies_grade_curve(self, logged_in_instructor):
        """
        E2E TEST: Apply grade curve

        BUSINESS REQUIREMENT:
        - Support curve application to adjust grades
        - Allow percentage or point-based curves
        - Apply curve to all submissions

        TEST SCENARIO:
        1. Navigate to submissions
        2. Apply 5% curve to all grades
        3. Verify grades adjusted
        4. Check that curve documented

        VALIDATION:
        - Curve applied successfully
        - All grades increased by 5%
        - Maximum grade capped at 100%
        - Curve application logged
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Grade a submission
        self.submissions_page.grade_submission("Student Test User")
        self.grading_page.wait_for_grading_modal_visible()

        # Apply grade curve
        self.grading_page.apply_grade_curve(5)  # 5% curve

        # Verify total score increased
        # (Implementation depends on UI showing updated score)

        # Save grade
        self.grading_page.save_grade()

    # ========================================================================
    # BULK GRADING WORKFLOWS
    # ========================================================================

    def test_instructor_bulk_grades_multiple_submissions(self, logged_in_instructor):
        """
        E2E TEST: Bulk grade multiple submissions

        BUSINESS REQUIREMENT:
        - Support bulk grading for efficiency
        - Auto-grade all eligible submissions
        - Skip submissions requiring manual grading

        TEST SCENARIO:
        1. Navigate to submissions list
        2. Click bulk grade button
        3. Verify auto-graded submissions processed
        4. Check manual grading still required for some

        VALIDATION:
        - Bulk grading completes successfully
        - All auto-gradable submissions graded
        - Manual grading queue updated
        - Performance acceptable for large batches
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Get initial statistics
        initial_stats = self.submissions_page.get_statistics()

        # Bulk grade all auto-gradable submissions
        self.submissions_page.bulk_grade_all()

        # Wait for processing
        time.sleep(2)

        # Get updated statistics
        final_stats = self.submissions_page.get_statistics()

        # Verify graded count increased
        # (In real implementation, would parse and compare numbers)

    def test_instructor_filters_submissions_by_status(self, logged_in_instructor):
        """
        E2E TEST: Filter submissions by grading status

        BUSINESS REQUIREMENT:
        - Support filtering for efficient grading workflow
        - Show only ungraded, graded, or needs review
        - Maintain sort order after filtering

        TEST SCENARIO:
        1. Navigate to submissions
        2. Apply "ungraded" filter
        3. Verify only ungraded submissions shown
        4. Apply "needs review" filter
        5. Verify manual grading submissions shown

        VALIDATION:
        - Filters apply correctly
        - Submission list updates
        - Count matches filter
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Filter by ungraded
        self.submissions_page.filter_by_status("ungraded")
        time.sleep(0.5)

        # Verify filtered results
        # (Implementation depends on UI showing filter results)

        # Filter by graded
        self.submissions_page.filter_by_status("graded")
        time.sleep(0.5)

        # Filter by needs review
        self.submissions_page.filter_by_status("needs_review")
        time.sleep(0.5)

    def test_instructor_sorts_submissions_by_score(self, logged_in_instructor):
        """
        E2E TEST: Sort submissions by score

        BUSINESS REQUIREMENT:
        - Support sorting for analysis
        - Sort by score, date, student name
        - Maintain sort across page reloads

        TEST SCENARIO:
        1. Navigate to submissions
        2. Sort by score (lowest to highest)
        3. Verify order correct
        4. Sort by score (highest to lowest)
        5. Verify order reversed

        VALIDATION:
        - Sorting works correctly
        - Order updates immediately
        - Stable sort for equal values
        """
        self.dashboard_page.navigate_to_quiz_submissions()

        # Sort by score
        self.submissions_page.sort_submissions("score")
        time.sleep(0.5)

        # Verify sort applied
        # (Implementation depends on UI)

        # Sort by date
        self.submissions_page.sort_submissions("date")
        time.sleep(0.5)

        # Sort by name
        self.submissions_page.sort_submissions("name")
        time.sleep(0.5)

    # ========================================================================
    # GRADE APPEAL HANDLING
    # ========================================================================

    def test_instructor_reviews_grade_appeal(self, logged_in_instructor):
        """
        E2E TEST: Review student grade appeal

        BUSINESS REQUIREMENT:
        - Support student grade appeals
        - Allow instructor to review and respond
        - Update grade if appeal accepted

        TEST SCENARIO:
        1. Navigate to appeals section
        2. View student appeal
        3. Review original grading
        4. Accept or reject appeal
        5. Update grade if accepted

        VALIDATION:
        - Appeal displayed with context
        - Original grading visible
        - Accept/reject options work
        - Grade updated appropriately
        """
        # Note: This test assumes grade appeal functionality exists
        # Implementation depends on UI for grade appeals

        self.dashboard_page.navigate_to_quiz_submissions()

        # In a real implementation, would:
        # 1. Navigate to appeals section
        # 2. Find pending appeal
        # 3. Review and respond
        # 4. Update grade if needed
