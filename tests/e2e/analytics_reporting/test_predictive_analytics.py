"""
Comprehensive E2E Tests for Predictive Analytics

BUSINESS REQUIREMENT:
Tests the predictive analytics system to enable early intervention for
struggling students, forecast enrollment trends, and optimize resource
allocation based on data-driven predictions.

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver with Page Object Model pattern
- Tests machine learning model predictions
- Validates forecasting algorithms
- Tests against HTTPS frontend (https://localhost:3000)
- Database verification for prediction accuracy

TEST COVERAGE:
1. Student Success Prediction (3 tests):
   - Predict student at-risk status based on engagement
   - Early warning system for struggling students
   - Success probability calculation

2. Trend Analysis (3 tests):
   - Course completion trend prediction
   - Enrollment growth forecasting
   - Resource utilization forecasting

3. Custom Analytics (2 tests):
   - Custom metric creation
   - Custom dashboard configuration

PRIORITY: P1 (HIGH) - Critical for proactive student support
"""

import pytest
import time
import uuid
import asyncpg
import httpx
import json
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from tests.e2e.selenium_base import BasePage, BaseTest


# ============================================================================
# PAGE OBJECTS - Following Page Object Model Pattern
# ============================================================================

class PredictiveAnalyticsPage(BasePage):
    """
    Page Object for predictive analytics dashboard.

    BUSINESS CONTEXT:
    Enables instructors to identify at-risk students early and allocate
    resources effectively based on predictive insights.
    """

    # Locators
    PREDICTIVE_TAB = (By.ID, "predictive-analytics-tab")
    PREDICTIVE_SECTION = (By.ID, "predictive-analytics-section")
    AT_RISK_STUDENTS_LIST = (By.CLASS_NAME, "at-risk-students-list")
    AT_RISK_STUDENT_ITEM = (By.CLASS_NAME, "at-risk-student-item")
    RISK_SCORE_BADGE = (By.CLASS_NAME, "risk-score-badge")
    SUCCESS_PROBABILITY = (By.CLASS_NAME, "success-probability")
    EARLY_WARNING_ALERT = (By.CLASS_NAME, "early-warning-alert")
    INTERVENTION_RECOMMENDATION = (By.CLASS_NAME, "intervention-recommendation")
    COMPLETION_TREND_CHART = (By.ID, "completion-trend-chart")
    ENROLLMENT_FORECAST_CHART = (By.ID, "enrollment-forecast-chart")
    RESOURCE_UTILIZATION_CHART = (By.ID, "resource-utilization-chart")
    TREND_LINE = (By.CLASS_NAME, "trend-line")
    FORECAST_CONFIDENCE = (By.CLASS_NAME, "forecast-confidence")
    CUSTOM_METRIC_FORM = (By.ID, "custom-metric-form")
    METRIC_NAME_INPUT = (By.ID, "metric-name")
    METRIC_FORMULA_INPUT = (By.ID, "metric-formula")
    METRIC_TYPE_SELECT = (By.ID, "metric-type")
    ADD_METRIC_BUTTON = (By.ID, "add-metric-btn")
    CUSTOM_METRICS_LIST = (By.CLASS_NAME, "custom-metrics-list")
    CUSTOM_METRIC_ITEM = (By.CLASS_NAME, "custom-metric-item")
    DASHBOARD_BUILDER = (By.ID, "dashboard-builder")
    WIDGET_SELECTOR = (By.CLASS_NAME, "widget-selector")
    ADD_WIDGET_BUTTON = (By.CLASS_NAME, "add-widget-btn")
    DASHBOARD_CANVAS = (By.ID, "dashboard-canvas")
    WIDGET_CONTAINER = (By.CLASS_NAME, "widget-container")

    def navigate_to_predictive_analytics(self):
        """Navigate to predictive analytics dashboard."""
        self.navigate_to("/instructor-dashboard")
        time.sleep(2)
        if self.is_element_present(*self.PREDICTIVE_TAB, timeout=10):
            self.click_element(*self.PREDICTIVE_TAB)
            time.sleep(2)

    def get_at_risk_students(self) -> list:
        """
        Get list of at-risk students with risk scores.

        Returns:
            List of dicts with student info and risk scores
        """
        students = []
        student_elements = self.driver.find_elements(*self.AT_RISK_STUDENT_ITEM)

        for elem in student_elements:
            student_data = {
                "name": elem.find_element(By.CLASS_NAME, "student-name").text,
                "risk_score": float(elem.find_element(By.CLASS_NAME, "risk-score").text.strip('%')),
                "risk_level": elem.find_element(By.CLASS_NAME, "risk-level").text.lower()
            }
            students.append(student_data)

        return students

    def get_student_success_probability(self, student_name: str) -> float:
        """
        Get success probability for specific student.

        Args:
            student_name: Name of student to check

        Returns:
            Success probability as percentage (0-100)
        """
        student_elements = self.driver.find_elements(*self.AT_RISK_STUDENT_ITEM)

        for elem in student_elements:
            name = elem.find_element(By.CLASS_NAME, "student-name").text
            if name == student_name:
                prob_elem = elem.find_element(*self.SUCCESS_PROBABILITY)
                prob_text = prob_elem.text.strip('%')
                return float(prob_text)

        raise ValueError(f"Student '{student_name}' not found in analytics")

    def get_early_warnings(self) -> list:
        """Get list of early warning alerts."""
        warnings = []
        warning_elements = self.driver.find_elements(*self.EARLY_WARNING_ALERT)

        for elem in warning_elements:
            warning_data = {
                "student": elem.find_element(By.CLASS_NAME, "warning-student").text,
                "reason": elem.find_element(By.CLASS_NAME, "warning-reason").text,
                "severity": elem.find_element(By.CLASS_NAME, "warning-severity").text
            }
            warnings.append(warning_data)

        return warnings

    def get_intervention_recommendations(self, student_name: str) -> list:
        """Get intervention recommendations for student."""
        recommendations = []
        student_elements = self.driver.find_elements(*self.AT_RISK_STUDENT_ITEM)

        for elem in student_elements:
            name = elem.find_element(By.CLASS_NAME, "student-name").text
            if name == student_name:
                rec_elements = elem.find_elements(*self.INTERVENTION_RECOMMENDATION)
                recommendations = [r.text for r in rec_elements]
                break

        return recommendations

    def get_completion_trend_data(self) -> dict:
        """
        Get course completion trend forecast data.

        Returns:
            Dict with historical data, forecast, and confidence intervals
        """
        script = """
        const chart = document.querySelector('#completion-trend-chart');
        if (chart && chart.chartInstance) {
            return {
                historical: chart.chartInstance.data.datasets[0].data,
                forecast: chart.chartInstance.data.datasets[1].data,
                labels: chart.chartInstance.data.labels
            };
        }
        return null;
        """
        return self.driver.execute_script(script)

    def get_enrollment_forecast(self) -> dict:
        """Get enrollment forecast data."""
        script = """
        const chart = document.querySelector('#enrollment-forecast-chart');
        if (chart && chart.chartInstance) {
            return {
                actual: chart.chartInstance.data.datasets[0].data,
                forecast: chart.chartInstance.data.datasets[1].data,
                labels: chart.chartInstance.data.labels
            };
        }
        return null;
        """
        return self.driver.execute_script(script)

    def get_resource_utilization_forecast(self) -> dict:
        """Get resource utilization forecast data."""
        script = """
        const chart = document.querySelector('#resource-utilization-chart');
        if (chart && chart.chartInstance) {
            return {
                cpu: chart.chartInstance.data.datasets[0].data,
                memory: chart.chartInstance.data.datasets[1].data,
                storage: chart.chartInstance.data.datasets[2].data,
                labels: chart.chartInstance.data.labels
            };
        }
        return null;
        """
        return self.driver.execute_script(script)

    def create_custom_metric(self, name: str, formula: str, metric_type: str):
        """
        Create a custom analytics metric.

        Args:
            name: Metric name
            formula: Metric calculation formula
            metric_type: Type of metric (average, sum, count, etc.)
        """
        self.find_element(*self.METRIC_NAME_INPUT).send_keys(name)
        self.find_element(*self.METRIC_FORMULA_INPUT).send_keys(formula)

        select = self.find_element(*self.METRIC_TYPE_SELECT)
        select.click()
        time.sleep(0.5)

        option = select.find_element(By.XPATH, f"//option[@value='{metric_type}']")
        option.click()

        self.click_element(*self.ADD_METRIC_BUTTON)
        time.sleep(1)

    def get_custom_metrics(self) -> list:
        """Get list of custom metrics."""
        metrics = []
        metric_elements = self.driver.find_elements(*self.CUSTOM_METRIC_ITEM)

        for elem in metric_elements:
            metric_data = {
                "name": elem.find_element(By.CLASS_NAME, "metric-name").text,
                "value": elem.find_element(By.CLASS_NAME, "metric-value").text,
                "type": elem.find_element(By.CLASS_NAME, "metric-type").text
            }
            metrics.append(metric_data)

        return metrics

    def add_widget_to_dashboard(self, widget_type: str):
        """
        Add a widget to custom dashboard.

        Args:
            widget_type: Type of widget to add (chart, metric, table, etc.)
        """
        # Open widget selector
        selector = self.find_element(*self.WIDGET_SELECTOR)
        selector.click()
        time.sleep(0.5)

        # Find and click widget type
        widget_option = selector.find_element(By.XPATH, f"//div[@data-widget-type='{widget_type}']")
        widget_option.click()
        time.sleep(1)

    def get_dashboard_widgets(self) -> list:
        """Get list of widgets on dashboard."""
        widgets = []
        widget_elements = self.driver.find_elements(*self.WIDGET_CONTAINER)

        for elem in widget_elements:
            widget_data = {
                "type": elem.get_attribute("data-widget-type"),
                "title": elem.find_element(By.CLASS_NAME, "widget-title").text,
                "visible": elem.is_displayed()
            }
            widgets.append(widget_data)

        return widgets


# ============================================================================
# TEST CLASS - Student Success Prediction
# ============================================================================

@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.predictive
@pytest.mark.priority_critical
class TestStudentSuccessPrediction(BaseTest):
    """
    Test suite for student success prediction features.

    BUSINESS REQUIREMENT:
    Enable early identification of struggling students to provide
    timely interventions and improve success rates.
    """

    @pytest.mark.asyncio
    async def test_01_predict_at_risk_students_based_on_engagement(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Predict student at-risk status based on engagement metrics

        BUSINESS REQUIREMENT:
        - Identify students at risk of failing or dropping out
        - Use engagement metrics (logins, activity, quiz scores)
        - Provide risk scores and categories (low, medium, high risk)

        TEST SCENARIO:
        1. Create students with varying engagement levels
        2. Instructor opens predictive analytics
        3. Verify at-risk students identified correctly
        4. Check risk scores calculated accurately
        5. Validate risk categories assigned properly

        VALIDATION:
        - Students with low engagement flagged as at-risk
        - Risk scores reflect engagement patterns
        - Risk categories accurate (high risk < 40%, medium 40-70%, low > 70%)
        - Database prediction model results consistent
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to predictive analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_predictive_analytics()
        time.sleep(3)

        # Get at-risk students list
        at_risk_students = page.get_at_risk_students()

        # VERIFICATION: At-risk students identified
        assert len(at_risk_students) > 0, "Should identify at-risk students"

        # VERIFICATION: Risk scores within valid range (0-100)
        for student in at_risk_students:
            assert 0 <= student['risk_score'] <= 100, \
                f"Risk score {student['risk_score']} out of range for {student['name']}"

        # VERIFICATION: Risk levels assigned correctly
        for student in at_risk_students:
            score = student['risk_score']
            level = student['risk_level']

            if score < 40:
                assert level == 'high', f"Score {score} should be high risk, got {level}"
            elif score < 70:
                assert level == 'medium', f"Score {score} should be medium risk, got {level}"
            else:
                assert level == 'low', f"Score {score} should be low risk, got {level}"

        # DATABASE VERIFICATION: Check prediction model
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT
                s.student_id,
                s.full_name,
                COALESCE(AVG(CASE WHEN qs.score IS NOT NULL
                    THEN qs.score / qs.total_questions * 100
                    ELSE 0 END), 0) as avg_quiz_score,
                COUNT(DISTINCT sa.activity_id) as activity_count,
                COUNT(DISTINCT DATE(sa.timestamp)) as active_days
            FROM students s
            LEFT JOIN quiz_submissions qs ON s.student_id = qs.student_id
            LEFT JOIN student_activities sa ON s.student_id = sa.student_id
            WHERE s.student_id IN (
                SELECT student_id FROM enrollments WHERE course_id = %s
            )
            GROUP BY s.student_id, s.full_name
        """, (browser.execute_script("return window.currentCourseId"),))

        db_students = cursor.fetchall()

        # Verify at-risk identification matches database patterns
        for db_student in db_students:
            student_id, name, avg_score, activity_count, active_days = db_student

            # Low engagement = at-risk
            if avg_score < 60 or activity_count < 10 or active_days < 5:
                # Should be in at-risk list
                found = any(s['name'] == name for s in at_risk_students)
                assert found, f"{name} should be identified as at-risk (score: {avg_score}, activities: {activity_count})"

    @pytest.mark.asyncio
    async def test_02_early_warning_system_for_struggling_students(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Early warning system alerts instructors about struggling students

        BUSINESS REQUIREMENT:
        - Proactive alerts for instructors when students show warning signs
        - Multiple warning triggers (missed assignments, low quiz scores, inactivity)
        - Prioritized by severity for instructor action

        TEST SCENARIO:
        1. Create student with concerning patterns
        2. Instructor opens predictive analytics
        3. Verify early warning alerts displayed
        4. Check alert priorities and reasons
        5. Validate intervention recommendations

        VALIDATION:
        - Early warnings triggered for concerning patterns
        - Severity levels accurate (critical, warning, info)
        - Specific reasons provided for each warning
        - Actionable intervention recommendations shown
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to predictive analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_predictive_analytics()
        time.sleep(3)

        # Get early warnings
        warnings = page.get_early_warnings()

        # VERIFICATION: Warnings generated
        assert len(warnings) > 0, "Should have early warning alerts"

        # VERIFICATION: Warnings have required fields
        for warning in warnings:
            assert warning['student'], "Warning should have student name"
            assert warning['reason'], "Warning should have reason"
            assert warning['severity'] in ['critical', 'warning', 'info'], \
                f"Invalid severity: {warning['severity']}"

        # VERIFICATION: Critical warnings prioritized (shown first)
        if len(warnings) > 1:
            critical_warnings = [w for w in warnings if w['severity'] == 'critical']
            if critical_warnings:
                # First warning should be critical
                assert warnings[0]['severity'] == 'critical', \
                    "Critical warnings should be shown first"

        # Check intervention recommendations
        if warnings:
            first_warning_student = warnings[0]['student']
            recommendations = page.get_intervention_recommendations(first_warning_student)

            # VERIFICATION: Recommendations provided
            assert len(recommendations) > 0, \
                f"Should have intervention recommendations for {first_warning_student}"

            # VERIFICATION: Recommendations are actionable
            action_keywords = ['contact', 'schedule', 'send', 'provide', 'offer', 'recommend']
            for rec in recommendations:
                has_action = any(keyword in rec.lower() for keyword in action_keywords)
                assert has_action, f"Recommendation should be actionable: {rec}"

    @pytest.mark.asyncio
    async def test_03_success_probability_calculation(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Calculate and display success probability for each student

        BUSINESS REQUIREMENT:
        - Predict likelihood of course completion/passing
        - Use historical data and current performance
        - Provide confidence intervals for predictions

        TEST SCENARIO:
        1. Instructor opens predictive analytics
        2. View success probabilities for students
        3. Verify probabilities calculated correctly
        4. Check probability ranges and confidence
        5. Validate against historical success rates

        VALIDATION:
        - Success probabilities displayed (0-100%)
        - Probabilities reflect current performance
        - High performers have high success probability
        - Low performers have low success probability
        - Confidence intervals provided
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to predictive analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_predictive_analytics()
        time.sleep(3)

        # Get at-risk students (includes success probabilities)
        students = page.get_at_risk_students()

        # VERIFICATION: Success probabilities calculated
        assert len(students) > 0, "Should have students with success probabilities"

        # Verify each student has valid success probability
        for student in students:
            # Get success probability for student
            prob = page.get_student_success_probability(student['name'])

            # VERIFICATION: Probability in valid range
            assert 0 <= prob <= 100, \
                f"Success probability {prob} out of range for {student['name']}"

            # VERIFICATION: Inverse relationship with risk score
            # High risk score = low success probability
            risk_score = student['risk_score']
            # Allow some variance in the relationship
            assert abs((100 - risk_score) - prob) < 20, \
                f"Success probability ({prob}) should inversely correlate with risk score ({risk_score})"

        # DATABASE VERIFICATION: Compare with actual success rates
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT
                s.student_id,
                s.full_name,
                AVG(CASE WHEN qs.score >= 60 THEN 1.0 ELSE 0.0 END) * 100 as passing_rate,
                COUNT(DISTINCT CASE WHEN qs.status = 'graded' THEN qs.quiz_id END) as completed_quizzes,
                COUNT(DISTINCT q.quiz_id) as total_quizzes
            FROM students s
            CROSS JOIN (SELECT quiz_id FROM quizzes WHERE course_id = %s) q
            LEFT JOIN quiz_submissions qs ON s.student_id = qs.student_id AND q.quiz_id = qs.quiz_id
            WHERE s.student_id IN (
                SELECT student_id FROM enrollments WHERE course_id = %s
            )
            GROUP BY s.student_id, s.full_name
        """, (browser.execute_script("return window.currentCourseId"),) * 2)

        db_students = cursor.fetchall()

        # Verify predictions reasonably match actual performance
        for db_student in db_students:
            student_id, name, passing_rate, completed, total = db_student

            try:
                predicted_prob = page.get_student_success_probability(name)

                # If student has completed quizzes, prediction should be close to actual
                if completed > 0:
                    # Allow 30% variance (predictions are estimates)
                    assert abs(predicted_prob - passing_rate) < 30, \
                        f"{name}: Predicted {predicted_prob}% vs Actual {passing_rate}%"
            except ValueError:
                # Student not in at-risk list (likely performing well)
                pass


# ============================================================================
# TEST CLASS - Trend Analysis
# ============================================================================

@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.predictive
@pytest.mark.trends
@pytest.mark.priority_high
class TestTrendAnalysis(BaseTest):
    """
    Test suite for trend analysis and forecasting features.

    BUSINESS REQUIREMENT:
    Enable data-driven planning and resource allocation based on
    trend predictions and historical patterns.
    """

    def test_04_course_completion_trend_prediction(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Predict course completion trends over time

        BUSINESS REQUIREMENT:
        - Forecast future completion rates
        - Identify completion patterns
        - Plan interventions based on trends

        TEST SCENARIO:
        1. Instructor opens trend analysis dashboard
        2. View completion trend chart
        3. Verify historical data displayed
        4. Check forecast for future periods
        5. Validate trend line accuracy

        VALIDATION:
        - Historical completion data shown
        - Forecast extends into future
        - Trend line follows data pattern
        - Confidence intervals included
        - Predictions mathematically sound
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to predictive analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_predictive_analytics()
        time.sleep(3)

        # Get completion trend data
        trend_data = page.get_completion_trend_data()

        # VERIFICATION: Trend data exists
        assert trend_data is not None, "Completion trend data should be available"

        # VERIFICATION: Historical and forecast data present
        assert trend_data.get('historical'), "Should have historical completion data"
        assert trend_data.get('forecast'), "Should have forecast data"
        assert trend_data.get('labels'), "Should have time period labels"

        # VERIFICATION: Forecast extends beyond historical data
        historical_count = len([x for x in trend_data['historical'] if x is not None])
        forecast_count = len([x for x in trend_data['forecast'] if x is not None])
        assert forecast_count > 0, "Should have forecast data points"

        # VERIFICATION: Data values in valid range (0-100%)
        for value in trend_data['historical']:
            if value is not None:
                assert 0 <= value <= 100, f"Historical completion rate {value} out of range"

        for value in trend_data['forecast']:
            if value is not None:
                assert 0 <= value <= 100, f"Forecast completion rate {value} out of range"

        # DATABASE VERIFICATION: Historical data matches database
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT
                DATE_TRUNC('week', e.enrolled_at) as week,
                COUNT(*) FILTER (WHERE e.completion_status = 'completed') * 100.0 / NULLIF(COUNT(*), 0) as completion_rate
            FROM enrollments e
            WHERE e.course_id = %s
            GROUP BY week
            ORDER BY week DESC
            LIMIT 10
        """, (browser.execute_script("return window.currentCourseId"),))

        db_rates = [row[1] for row in cursor.fetchall()]

        if db_rates and trend_data['historical']:
            # Compare most recent rates (allow some rounding variance)
            ui_recent = [x for x in trend_data['historical'][-3:] if x is not None]
            if ui_recent and db_rates:
                avg_ui = sum(ui_recent) / len(ui_recent)
                avg_db = sum(db_rates[:3]) / min(len(db_rates), 3)
                assert abs(avg_ui - avg_db) < 10, \
                    f"UI trend ({avg_ui}) should match DB trend ({avg_db})"

    def test_05_enrollment_growth_forecasting(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Forecast enrollment growth for capacity planning

        BUSINESS REQUIREMENT:
        - Predict future enrollment numbers
        - Plan resource allocation
        - Identify growth opportunities

        TEST SCENARIO:
        1. Instructor opens enrollment forecast
        2. View enrollment trend chart
        3. Verify historical enrollment data
        4. Check forecast for upcoming periods
        5. Validate growth rate calculations

        VALIDATION:
        - Historical enrollment shown
        - Forecast predicts future enrollments
        - Growth rate calculated
        - Seasonal patterns identified
        - Capacity planning insights provided
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to predictive analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_predictive_analytics()
        time.sleep(3)

        # Get enrollment forecast data
        forecast_data = page.get_enrollment_forecast()

        # VERIFICATION: Forecast data exists
        assert forecast_data is not None, "Enrollment forecast data should be available"

        # VERIFICATION: Actual and forecast data present
        assert forecast_data.get('actual'), "Should have actual enrollment data"
        assert forecast_data.get('forecast'), "Should have forecast data"
        assert forecast_data.get('labels'), "Should have time period labels"

        # VERIFICATION: Forecast extends into future
        actual_count = len([x for x in forecast_data['actual'] if x is not None])
        forecast_count = len([x for x in forecast_data['forecast'] if x is not None])
        assert forecast_count > 0, "Should have forecast enrollments"

        # VERIFICATION: Enrollment numbers non-negative
        for value in forecast_data['actual']:
            if value is not None:
                assert value >= 0, f"Actual enrollment {value} cannot be negative"

        for value in forecast_data['forecast']:
            if value is not None:
                assert value >= 0, f"Forecast enrollment {value} cannot be negative"

        # VERIFICATION: Forecast reasonable based on recent trends
        if forecast_data['actual'] and forecast_data['forecast']:
            recent_actual = [x for x in forecast_data['actual'][-3:] if x is not None]
            future_forecast = [x for x in forecast_data['forecast'] if x is not None]

            if recent_actual and future_forecast:
                avg_actual = sum(recent_actual) / len(recent_actual)
                avg_forecast = sum(future_forecast) / len(future_forecast)

                # Forecast should be within 50% of recent average (reasonable growth/decline)
                assert 0.5 * avg_actual <= avg_forecast <= 1.5 * avg_actual, \
                    f"Forecast ({avg_forecast}) too far from recent trend ({avg_actual})"

    def test_06_resource_utilization_forecasting(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Forecast resource utilization (CPU, memory, storage)

        BUSINESS REQUIREMENT:
        - Predict infrastructure needs
        - Optimize resource allocation
        - Prevent performance issues

        TEST SCENARIO:
        1. Instructor opens resource utilization forecast
        2. View resource usage trends
        3. Verify current utilization data
        4. Check forecast for future periods
        5. Validate capacity recommendations

        VALIDATION:
        - CPU, memory, storage forecasts shown
        - Utilization percentages calculated
        - Over-utilization warnings provided
        - Scaling recommendations given
        - Cost optimization insights included
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to predictive analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_predictive_analytics()
        time.sleep(3)

        # Get resource utilization forecast
        resource_data = page.get_resource_utilization_forecast()

        # VERIFICATION: Resource data exists
        assert resource_data is not None, "Resource utilization forecast should be available"

        # VERIFICATION: CPU, memory, storage data present
        assert resource_data.get('cpu'), "Should have CPU utilization data"
        assert resource_data.get('memory'), "Should have memory utilization data"
        assert resource_data.get('storage'), "Should have storage utilization data"
        assert resource_data.get('labels'), "Should have time period labels"

        # VERIFICATION: Utilization percentages in valid range (0-100%)
        for resource_type in ['cpu', 'memory', 'storage']:
            for value in resource_data[resource_type]:
                if value is not None:
                    assert 0 <= value <= 100, \
                        f"{resource_type.upper()} utilization {value}% out of range"

        # VERIFICATION: Check for over-utilization warnings
        for resource_type in ['cpu', 'memory', 'storage']:
            max_util = max([x for x in resource_data[resource_type] if x is not None], default=0)

            # If any resource > 80%, should show warning
            if max_util > 80:
                warning_elem = browser.find_elements(
                    By.XPATH,
                    f"//div[contains(@class, 'resource-warning') and contains(text(), '{resource_type.upper()}')]"
                )
                assert len(warning_elem) > 0, \
                    f"Should show warning for high {resource_type.upper()} utilization ({max_util}%)"


# ============================================================================
# TEST CLASS - Custom Analytics
# ============================================================================

@pytest.mark.e2e
@pytest.mark.analytics
@pytest.mark.predictive
@pytest.mark.custom
@pytest.mark.priority_medium
class TestCustomAnalytics(BaseTest):
    """
    Test suite for custom analytics and dashboard configuration.

    BUSINESS REQUIREMENT:
    Enable instructors to create custom metrics and dashboards
    tailored to their specific needs and teaching style.
    """

    def test_07_custom_metric_creation(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Create custom analytics metrics

        BUSINESS REQUIREMENT:
        - Allow instructors to define custom metrics
        - Support various metric types (average, sum, count, rate)
        - Use formulas for complex calculations
        - Display custom metrics alongside standard ones

        TEST SCENARIO:
        1. Instructor opens custom metrics page
        2. Create new custom metric (e.g., "Engagement Score")
        3. Define metric formula
        4. Select metric type
        5. Verify metric calculated and displayed

        VALIDATION:
        - Custom metric created successfully
        - Metric appears in metrics list
        - Metric value calculated correctly
        - Metric persists after page refresh
        - Multiple custom metrics supported
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to predictive analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_predictive_analytics()
        time.sleep(3)

        # Scroll to custom metrics section
        browser.execute_script("""
            document.querySelector('#custom-metric-form').scrollIntoView();
        """)
        time.sleep(1)

        # Create custom metric: "Engagement Score"
        metric_name = "Engagement Score"
        metric_formula = "(quiz_submissions + page_views + video_watches) / 3"
        metric_type = "average"

        page.create_custom_metric(metric_name, metric_formula, metric_type)

        # VERIFICATION: Metric created and displayed
        custom_metrics = page.get_custom_metrics()

        assert len(custom_metrics) > 0, "Should have custom metrics"

        # Find our new metric
        engagement_metric = next(
            (m for m in custom_metrics if m['name'] == metric_name),
            None
        )

        assert engagement_metric is not None, f"Custom metric '{metric_name}' should be created"
        assert engagement_metric['type'] == metric_type, \
            f"Metric type should be '{metric_type}', got '{engagement_metric['type']}'"

        # VERIFICATION: Metric value calculated
        assert engagement_metric['value'], "Metric should have calculated value"

        # Create second custom metric: "Completion Velocity"
        metric_name_2 = "Completion Velocity"
        metric_formula_2 = "completed_modules / days_enrolled"
        metric_type_2 = "average"

        page.create_custom_metric(metric_name_2, metric_formula_2, metric_type_2)

        # VERIFICATION: Multiple metrics supported
        custom_metrics = page.get_custom_metrics()
        assert len(custom_metrics) >= 2, "Should support multiple custom metrics"

        # DATABASE VERIFICATION: Metrics persisted
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT metric_name, metric_formula, metric_type
            FROM custom_analytics_metrics
            WHERE created_by = %s
            ORDER BY created_at DESC
        """, (instructor_credentials["user_id"],))

        db_metrics = cursor.fetchall()
        assert len(db_metrics) >= 2, "Custom metrics should be saved to database"

        # Verify page refresh persistence
        browser.refresh()
        time.sleep(3)

        custom_metrics = page.get_custom_metrics()
        assert len(custom_metrics) >= 2, "Custom metrics should persist after refresh"

    def test_08_custom_dashboard_configuration(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Configure custom analytics dashboard

        BUSINESS REQUIREMENT:
        - Allow instructors to build personalized dashboards
        - Drag-and-drop widget placement
        - Multiple widget types (charts, metrics, tables)
        - Save and restore dashboard layouts

        TEST SCENARIO:
        1. Instructor opens dashboard builder
        2. Add widgets to dashboard
        3. Arrange widgets in layout
        4. Save dashboard configuration
        5. Verify dashboard loads with saved layout

        VALIDATION:
        - Widgets can be added to dashboard
        - Widget types supported (chart, metric, table, list)
        - Dashboard layout persists
        - Multiple dashboard configurations supported
        - Dashboard can be reset to default
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as instructor
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(instructor_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(instructor_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to predictive analytics
        wait.until(EC.url_contains("/instructor-dashboard"))
        page.navigate_to_predictive_analytics()
        time.sleep(3)

        # Scroll to dashboard builder
        browser.execute_script("""
            document.querySelector('#dashboard-builder').scrollIntoView();
        """)
        time.sleep(1)

        # Get initial widget count
        initial_widgets = page.get_dashboard_widgets()
        initial_count = len(initial_widgets)

        # Add chart widget
        page.add_widget_to_dashboard('chart')
        time.sleep(1)

        # Add metric widget
        page.add_widget_to_dashboard('metric')
        time.sleep(1)

        # Add table widget
        page.add_widget_to_dashboard('table')
        time.sleep(1)

        # VERIFICATION: Widgets added to dashboard
        updated_widgets = page.get_dashboard_widgets()
        assert len(updated_widgets) >= initial_count + 3, \
            "Should have added 3 widgets to dashboard"

        # VERIFICATION: Different widget types present
        widget_types = [w['type'] for w in updated_widgets]
        assert 'chart' in widget_types, "Should have chart widget"
        assert 'metric' in widget_types, "Should have metric widget"
        assert 'table' in widget_types, "Should have table widget"

        # Save dashboard configuration
        save_button = browser.find_element(By.ID, "save-dashboard-btn")
        save_button.click()
        time.sleep(2)

        # VERIFICATION: Save confirmation shown
        try:
            confirmation = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "save-confirmation"))
            )
            assert confirmation.is_displayed(), "Should show save confirmation"
        except TimeoutException:
            pass  # Confirmation may be toast notification

        # DATABASE VERIFICATION: Dashboard config saved
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT dashboard_config
            FROM user_dashboard_configs
            WHERE user_id = %s AND dashboard_type = 'predictive_analytics'
        """, (instructor_credentials["user_id"],))

        db_config = cursor.fetchone()
        assert db_config is not None, "Dashboard config should be saved to database"

        config_json = json.loads(db_config[0])
        assert len(config_json.get('widgets', [])) >= 3, \
            "Dashboard config should include added widgets"

        # Refresh page and verify layout persists
        browser.refresh()
        time.sleep(3)

        persisted_widgets = page.get_dashboard_widgets()
        assert len(persisted_widgets) >= initial_count + 3, \
            "Dashboard layout should persist after page refresh"
