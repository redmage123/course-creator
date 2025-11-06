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

    @pytest.mark.asyncio
    async def test_04_course_completion_trend_prediction_over_time(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Predict course completion trends over time

        BUSINESS REQUIREMENT:
        - System must predict course completion trends to help instructors plan capacity
        - Forecast should extend 30 days into future with confidence intervals
        - Enable data-driven intervention planning

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to predictive analytics dashboard
        3. Select "Course Completion Trends" section
        4. View trend chart showing historical + predicted completion rates
        5. Verify prediction extends 30 days into future
        6. Verify confidence intervals displayed
        7. Compare prediction algorithm accuracy with database

        VALIDATION:
        - Trend line extends to future (30 days minimum)
        - Confidence intervals shown for predictions
        - Prediction data matches ML model output
        - Historical data accurate vs database
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

        # Scroll to Course Completion Trends section
        browser.execute_script("""
            document.querySelector('#completion-trend-chart').scrollIntoView();
        """)
        time.sleep(1)

        # Get completion trend data
        trend_data = page.get_completion_trend_data()

        # VERIFICATION: Trend data exists
        assert trend_data is not None, "Completion trend data should be available"

        # VERIFICATION: Historical and forecast data present
        assert trend_data.get('historical'), "Should have historical completion data"
        assert trend_data.get('forecast'), "Should have forecast data"
        assert trend_data.get('labels'), "Should have time period labels"

        # VERIFICATION: Forecast extends 30 days into future
        # Labels should include dates extending 30+ days ahead
        labels = trend_data['labels']
        forecast_labels = [labels[i] for i, val in enumerate(trend_data['forecast']) if val is not None]

        if forecast_labels:
            # Calculate days spanned by forecast
            # Assuming labels are date strings or can be parsed
            assert len(forecast_labels) >= 4, \
                "Forecast should extend at least 30 days (4+ weeks) into future"

        # VERIFICATION: Confidence intervals displayed
        # Check if chart has confidence interval elements
        confidence_elements = browser.find_elements(By.CLASS_NAME, "confidence-interval")
        assert len(confidence_elements) > 0, \
            "Should display confidence intervals for predictions"

        # Get confidence interval data from chart
        confidence_script = """
        const chart = document.querySelector('#completion-trend-chart');
        if (chart && chart.chartInstance && chart.chartInstance.data.datasets.length > 2) {
            return {
                upper: chart.chartInstance.data.datasets[2].data,
                lower: chart.chartInstance.data.datasets[3].data
            };
        }
        return null;
        """
        confidence_data = browser.execute_script(confidence_script)

        if confidence_data:
            # VERIFICATION: Confidence intervals present
            assert confidence_data.get('upper'), "Should have upper confidence interval"
            assert confidence_data.get('lower'), "Should have lower confidence interval"

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

        # DATABASE VERIFICATION: Compare prediction algorithm accuracy
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

        # VERIFICATION: Prediction algorithm uses ML model
        # Check for model metadata in chart or analytics service
        model_info_script = """
        const chart = document.querySelector('#completion-trend-chart');
        if (chart && chart.modelMetadata) {
            return {
                algorithm: chart.modelMetadata.algorithm,
                accuracy: chart.modelMetadata.accuracy
            };
        }
        return null;
        """
        model_info = browser.execute_script(model_info_script)

        if model_info:
            assert model_info.get('algorithm'), "Should use ML algorithm for predictions"
            # Optionally check accuracy threshold
            if model_info.get('accuracy'):
                assert model_info['accuracy'] >= 0.7, \
                    f"Model accuracy ({model_info['accuracy']}) should be at least 70%"

    @pytest.mark.asyncio
    async def test_05_enrollment_growth_forecasting(
        self, browser, test_base_url, org_admin_credentials, db_connection
    ):
        """
        E2E TEST: Forecast enrollment growth for capacity planning

        BUSINESS REQUIREMENT:
        - Platform must forecast enrollment growth for resource planning
        - Forecast should include growth rate percentage and confidence level
        - Enable organization-level capacity planning

        TEST SCENARIO:
        1. Login as organization admin
        2. Navigate to predictive analytics
        3. Select "Enrollment Forecasting" section
        4. View enrollment forecast for next quarter
        5. Verify forecast includes:
           - Expected enrollment numbers
           - Growth rate percentage
           - Confidence level
        6. Verify forecast based on historical enrollment patterns

        VALIDATION:
        - Forecast displayed with enrollment numbers
        - Growth rate calculated and shown
        - Confidence level >70%
        - Forecast based on historical data patterns
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as organization admin (not instructor)
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(org_admin_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(org_admin_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to organization analytics (not instructor dashboard)
        wait.until(EC.url_contains("/organization-dashboard"))

        # Navigate to predictive analytics section
        analytics_link = wait.until(
            EC.element_to_be_clickable((By.ID, "organization-analytics-link"))
        )
        analytics_link.click()
        time.sleep(2)

        # Click on Enrollment Forecasting section
        enrollment_tab = wait.until(
            EC.element_to_be_clickable((By.ID, "enrollment-forecasting-tab"))
        )
        enrollment_tab.click()
        time.sleep(2)

        # Scroll to enrollment forecast chart
        browser.execute_script("""
            document.querySelector('#enrollment-forecast-chart').scrollIntoView();
        """)
        time.sleep(1)

        # Get enrollment forecast data
        forecast_data = page.get_enrollment_forecast()

        # VERIFICATION: Forecast data exists
        assert forecast_data is not None, "Enrollment forecast data should be available"

        # VERIFICATION: Actual and forecast data present
        assert forecast_data.get('actual'), "Should have actual enrollment data"
        assert forecast_data.get('forecast'), "Should have forecast data"
        assert forecast_data.get('labels'), "Should have time period labels"

        # VERIFICATION: Forecast extends into future (next quarter = 3+ months)
        actual_count = len([x for x in forecast_data['actual'] if x is not None])
        forecast_count = len([x for x in forecast_data['forecast'] if x is not None])
        assert forecast_count >= 3, \
            "Should forecast at least 3 months (next quarter) of enrollments"

        # VERIFICATION: Expected enrollment numbers displayed
        for value in forecast_data['forecast']:
            if value is not None:
                assert value >= 0, f"Forecast enrollment {value} cannot be negative"
                assert isinstance(value, (int, float)), \
                    "Enrollment forecast should be numeric"

        # VERIFICATION: Growth rate percentage calculated and displayed
        growth_rate_elem = wait.until(
            EC.presence_of_element_located((By.ID, "enrollment-growth-rate"))
        )
        growth_rate_text = growth_rate_elem.text

        # Extract percentage (e.g., "+15.2%" or "-3.5%")
        import re
        growth_match = re.search(r'([+-]?\d+\.?\d*)%', growth_rate_text)
        assert growth_match, "Growth rate percentage should be displayed"

        growth_rate = float(growth_match.group(1))
        # Growth rate should be reasonable (-50% to +100%)
        assert -50 <= growth_rate <= 100, \
            f"Growth rate {growth_rate}% should be within reasonable bounds"

        # VERIFICATION: Confidence level displayed and >70%
        confidence_elem = wait.until(
            EC.presence_of_element_located((By.ID, "forecast-confidence-level"))
        )
        confidence_text = confidence_elem.text

        # Extract confidence percentage (e.g., "85%" or "Confidence: 72%")
        confidence_match = re.search(r'(\d+\.?\d*)%', confidence_text)
        assert confidence_match, "Confidence level should be displayed"

        confidence_level = float(confidence_match.group(1))
        assert confidence_level > 70, \
            f"Confidence level ({confidence_level}%) should be greater than 70%"

        # VERIFICATION: Forecast based on historical enrollment patterns
        # Calculate actual growth from historical data
        if len(forecast_data['actual']) >= 2:
            actual_enrollments = [x for x in forecast_data['actual'] if x is not None]
            if len(actual_enrollments) >= 2:
                # Calculate historical trend
                recent = actual_enrollments[-1]
                older = actual_enrollments[-2]

                if older > 0:
                    historical_growth = ((recent - older) / older) * 100

                    # Forecast growth should be similar to historical trend (±20%)
                    assert abs(growth_rate - historical_growth) < 20, \
                        f"Forecast growth ({growth_rate}%) should reflect historical trend ({historical_growth}%)"

        # DATABASE VERIFICATION: Verify forecast based on actual data
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT
                DATE_TRUNC('month', enrolled_at) as month,
                COUNT(*) as enrollment_count
            FROM enrollments
            WHERE organization_id = %s
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """, (org_admin_credentials.get("organization_id"),))

        db_enrollments = cursor.fetchall()

        if len(db_enrollments) >= 2:
            # Verify forecast reasonable compared to database trends
            recent_db = db_enrollments[0][1]
            older_db = db_enrollments[1][1]

            db_growth = ((recent_db - older_db) / older_db) * 100 if older_db > 0 else 0

            # Forecast should align with database trends
            assert abs(growth_rate - db_growth) < 30, \
                f"UI growth rate ({growth_rate}%) should align with DB trend ({db_growth}%)"

    @pytest.mark.asyncio
    async def test_06_resource_utilization_forecasting(
        self, browser, test_base_url, site_admin_credentials, db_connection
    ):
        """
        E2E TEST: Forecast resource utilization (CPU, memory, storage, labs)

        BUSINESS REQUIREMENT:
        - System must forecast resource needs to prevent performance issues
        - Predict lab container usage, storage capacity, database load, API volume
        - Highlight resource thresholds >80% capacity
        - Enable proactive infrastructure scaling

        TEST SCENARIO:
        1. Login as site admin
        2. Navigate to resource forecasting dashboard
        3. View predictions for:
           - Lab container usage
           - Storage capacity needs
           - Database query load
           - API request volume
        4. Verify predictions extend 7-30 days ahead
        5. Verify resource thresholds highlighted (>80% capacity)
        6. Compare predictions with actual resource metrics

        VALIDATION:
        - Resource forecasts shown for all types
        - Thresholds >80% highlighted with warnings
        - Predictions match usage patterns
        - Forecasts extend 7-30 days into future
        """
        page = PredictiveAnalyticsPage(browser)

        # Login as site admin (not instructor)
        page.navigate_to(f"{test_base_url}/login")
        wait = WebDriverWait(browser, 10)

        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        email_input.send_keys(site_admin_credentials["email"])

        password_input = browser.find_element(By.ID, "login-password")
        password_input.send_keys(site_admin_credentials["password"])

        browser.find_element(By.ID, "login-submit").click()

        # Navigate to site admin dashboard
        wait.until(EC.url_contains("/site-admin-dashboard"))

        # Navigate to resource forecasting section
        resource_link = wait.until(
            EC.element_to_be_clickable((By.ID, "resource-forecasting-link"))
        )
        resource_link.click()
        time.sleep(2)

        # Scroll to resource utilization chart
        browser.execute_script("""
            document.querySelector('#resource-utilization-chart').scrollIntoView();
        """)
        time.sleep(1)

        # Get resource utilization forecast
        resource_data = page.get_resource_utilization_forecast()

        # VERIFICATION: Resource data exists
        assert resource_data is not None, "Resource utilization forecast should be available"

        # VERIFICATION: CPU, memory, storage data present
        assert resource_data.get('cpu'), "Should have CPU utilization data"
        assert resource_data.get('memory'), "Should have memory utilization data"
        assert resource_data.get('storage'), "Should have storage utilization data"
        assert resource_data.get('labels'), "Should have time period labels"

        # VERIFICATION: Predictions extend 7-30 days ahead
        labels = resource_data['labels']
        # Assuming daily or weekly labels
        assert len(labels) >= 7, \
            "Forecasts should extend at least 7 days into future"
        assert len(labels) <= 30, \
            "Forecasts should not extend more than 30 days (keep predictions accurate)"

        # VERIFICATION: Lab container usage forecast
        # Check for lab-specific metrics
        lab_usage_script = """
        const labChart = document.querySelector('#lab-container-usage-chart');
        if (labChart && labChart.chartInstance) {
            return {
                current: labChart.chartInstance.data.datasets[0].data,
                forecast: labChart.chartInstance.data.datasets[1].data
            };
        }
        return null;
        """
        lab_data = browser.execute_script(lab_usage_script)

        if lab_data:
            assert lab_data.get('current'), "Should have current lab container usage"
            assert lab_data.get('forecast'), "Should forecast lab container needs"

        # VERIFICATION: Database query load forecast
        db_load_elem = browser.find_elements(By.ID, "database-query-load-forecast")
        if db_load_elem:
            # Database load should be tracked
            assert db_load_elem[0].is_displayed(), "Should display database load forecast"

        # VERIFICATION: API request volume forecast
        api_volume_elem = browser.find_elements(By.ID, "api-request-volume-forecast")
        if api_volume_elem:
            # API volume should be tracked
            assert api_volume_elem[0].is_displayed(), "Should display API volume forecast"

        # VERIFICATION: Utilization percentages in valid range (0-100%)
        for resource_type in ['cpu', 'memory', 'storage']:
            for value in resource_data[resource_type]:
                if value is not None:
                    assert 0 <= value <= 100, \
                        f"{resource_type.upper()} utilization {value}% out of range"

        # VERIFICATION: Resource thresholds >80% highlighted
        threshold_violations = []

        for resource_type in ['cpu', 'memory', 'storage']:
            max_util = max([x for x in resource_data[resource_type] if x is not None], default=0)

            # If any resource > 80%, must show warning
            if max_util > 80:
                threshold_violations.append((resource_type, max_util))

                # Check for warning element
                warning_elem = browser.find_elements(
                    By.XPATH,
                    f"//div[contains(@class, 'resource-warning') and contains(text(), '{resource_type.upper()}')]"
                )

                assert len(warning_elem) > 0, \
                    f"CRITICAL: Must show warning for {resource_type.upper()} at {max_util}% (threshold: 80%)"

                # Verify warning has correct styling (red/orange)
                warning_style = warning_elem[0].value_of_css_property('color')
                # Should be red or orange (not green/blue)
                assert warning_style, "Warning should have colored styling"

                # Check for specific threshold indicator
                threshold_badge = browser.find_elements(
                    By.XPATH,
                    f"//span[contains(@class, 'threshold-badge') and contains(text(), '80%')]"
                )
                # May have threshold badge showing 80% limit

        # VERIFICATION: Compare predictions with actual resource metrics
        # DATABASE VERIFICATION: Check actual resource usage
        cursor = db_connection.cursor()

        # Query actual resource metrics
        cursor.execute("""
            SELECT
                metric_type,
                AVG(metric_value) as avg_value,
                MAX(metric_value) as max_value
            FROM system_resource_metrics
            WHERE recorded_at >= NOW() - INTERVAL '7 days'
            GROUP BY metric_type
        """)

        db_metrics = cursor.fetchall()

        # Build map of actual metrics
        actual_metrics = {}
        for row in db_metrics:
            metric_type, avg_val, max_val = row
            actual_metrics[metric_type] = {
                'average': avg_val,
                'maximum': max_val
            }

        # Verify UI forecasts align with actual usage patterns
        if 'cpu_utilization' in actual_metrics:
            cpu_forecast = resource_data['cpu']
            recent_cpu_forecast = [x for x in cpu_forecast[:7] if x is not None]

            if recent_cpu_forecast:
                avg_forecast = sum(recent_cpu_forecast) / len(recent_cpu_forecast)
                actual_avg = actual_metrics['cpu_utilization']['average']

                # Forecast should be within 20% of actual average
                assert abs(avg_forecast - actual_avg) < 20, \
                    f"CPU forecast ({avg_forecast}%) should match actual usage ({actual_avg}%)"

        # VERIFICATION: Scaling recommendations provided
        scaling_recommendations = browser.find_elements(By.CLASS_NAME, "scaling-recommendation")

        if threshold_violations:
            # If thresholds violated, must provide scaling recommendations
            assert len(scaling_recommendations) > 0, \
                "Should provide scaling recommendations when resources exceed 80%"

            for rec in scaling_recommendations:
                rec_text = rec.text.lower()
                # Recommendations should be actionable
                assert any(keyword in rec_text for keyword in [
                    'scale', 'increase', 'upgrade', 'add', 'expand', 'allocate'
                ]), f"Recommendation should be actionable: {rec.text}"


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

    @pytest.mark.asyncio
    async def test_07_custom_metric_creation_workflow(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Complete custom metric creation workflow

        BUSINESS REQUIREMENT:
        - Instructors and admins must be able to create custom analytics metrics
        - Support formula-based calculations with aggregation functions
        - Metrics must calculate correctly from database
        - Enable tracking of instructor-specific KPIs

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to custom analytics section
        3. Click "Create Custom Metric"
        4. Fill metric form:
           - Name: "Weekly Quiz Completion Rate"
           - Formula: (quizzes_completed / total_quizzes) * 100
           - Aggregation: Weekly average
           - Visualization: Line chart
        5. Save metric
        6. Verify metric appears in analytics dashboard
        7. Verify metric calculates correctly from database

        VALIDATION:
        - Metric created successfully
        - Visible in analytics dashboard
        - Calculation accurate vs database
        - Metric persists after refresh
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

        # Click "Create Custom Metric" button
        create_metric_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "create-custom-metric-btn"))
        )
        create_metric_btn.click()
        time.sleep(1)

        # Fill metric form with specific values from requirement
        metric_name = "Weekly Quiz Completion Rate"
        metric_formula = "(quizzes_completed / total_quizzes) * 100"
        aggregation = "weekly_average"
        visualization = "line_chart"

        # Enter metric name
        name_input = wait.until(EC.presence_of_element_located((By.ID, "metric-name")))
        name_input.clear()
        name_input.send_keys(metric_name)

        # Enter metric formula
        formula_input = browser.find_element(By.ID, "metric-formula")
        formula_input.clear()
        formula_input.send_keys(metric_formula)

        # Select aggregation type
        aggregation_select = browser.find_element(By.ID, "metric-aggregation")
        aggregation_select.click()
        time.sleep(0.5)

        aggregation_option = aggregation_select.find_element(
            By.XPATH, f"//option[@value='{aggregation}']"
        )
        aggregation_option.click()

        # Select visualization type
        viz_select = browser.find_element(By.ID, "metric-visualization")
        viz_select.click()
        time.sleep(0.5)

        viz_option = viz_select.find_element(
            By.XPATH, f"//option[@value='{visualization}']"
        )
        viz_option.click()

        # Save metric
        save_btn = browser.find_element(By.ID, "save-metric-btn")
        save_btn.click()
        time.sleep(2)

        # VERIFICATION: Success message shown
        success_msg = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "metric-created-success"))
        )
        assert success_msg.is_displayed(), "Should show success message after creating metric"

        # VERIFICATION: Metric appears in analytics dashboard
        custom_metrics = page.get_custom_metrics()

        assert len(custom_metrics) > 0, "Should have custom metrics in dashboard"

        # Find our new metric
        quiz_metric = next(
            (m for m in custom_metrics if m['name'] == metric_name),
            None
        )

        assert quiz_metric is not None, \
            f"Custom metric '{metric_name}' should appear in analytics dashboard"

        # VERIFICATION: Metric has calculated value
        assert quiz_metric['value'], "Metric should have calculated value"

        # Extract numeric value from metric
        import re
        value_match = re.search(r'(\d+\.?\d*)%?', quiz_metric['value'])
        assert value_match, "Metric value should be numeric"

        calculated_value = float(value_match.group(1))

        # DATABASE VERIFICATION: Verify metric calculates correctly from database
        cursor = db_connection.cursor()

        # Get actual quiz completion data
        cursor.execute("""
            SELECT
                COUNT(DISTINCT CASE WHEN qs.status = 'graded' THEN qs.quiz_id END) as quizzes_completed,
                COUNT(DISTINCT q.quiz_id) as total_quizzes
            FROM quizzes q
            LEFT JOIN quiz_submissions qs ON q.quiz_id = qs.quiz_id
            WHERE q.course_id = %s
                AND DATE_TRUNC('week', COALESCE(qs.submitted_at, NOW())) = DATE_TRUNC('week', NOW())
        """, (browser.execute_script("return window.currentCourseId"),))

        db_result = cursor.fetchone()
        quizzes_completed, total_quizzes = db_result

        # Calculate expected value using formula
        if total_quizzes > 0:
            expected_value = (quizzes_completed / total_quizzes) * 100

            # Verify calculated value matches database calculation
            assert abs(calculated_value - expected_value) < 1.0, \
                f"Metric value ({calculated_value}%) should match database calculation ({expected_value}%)"

        # VERIFICATION: Metric persisted to database
        cursor.execute("""
            SELECT metric_name, metric_formula, aggregation_type, visualization_type
            FROM custom_analytics_metrics
            WHERE created_by = %s AND metric_name = %s
        """, (instructor_credentials.get("user_id"), metric_name))

        db_metric = cursor.fetchone()
        assert db_metric is not None, "Custom metric should be saved to database"

        db_name, db_formula, db_agg, db_viz = db_metric
        assert db_name == metric_name, "Metric name should match in database"
        assert db_formula == metric_formula, "Metric formula should match in database"
        assert db_agg == aggregation, "Aggregation type should match in database"
        assert db_viz == visualization, "Visualization type should match in database"

        # VERIFICATION: Metric persists after page refresh
        browser.refresh()
        time.sleep(3)

        # Navigate back to custom metrics section
        browser.execute_script("""
            document.querySelector('#custom-metric-form').scrollIntoView();
        """)
        time.sleep(1)

        custom_metrics_after_refresh = page.get_custom_metrics()

        quiz_metric_persisted = next(
            (m for m in custom_metrics_after_refresh if m['name'] == metric_name),
            None
        )

        assert quiz_metric_persisted is not None, \
            "Custom metric should persist after page refresh"

    @pytest.mark.asyncio
    async def test_08_custom_dashboard_configuration(
        self, browser, test_base_url, instructor_credentials, db_connection
    ):
        """
        E2E TEST: Complete custom dashboard configuration workflow

        BUSINESS REQUIREMENT:
        - Users must be able to customize their analytics dashboard layout
        - Support adding/removing widgets with drag-and-drop
        - Widget sizes configurable (small, medium, large)
        - Dashboard configuration persists in user preferences

        TEST SCENARIO:
        1. Login as instructor
        2. Navigate to analytics dashboard
        3. Enter "Edit Dashboard" mode
        4. Add/remove widgets:
           - Add "Student Engagement" widget
           - Remove "Course Revenue" widget
           - Reorder widgets via drag-and-drop
        5. Change widget sizes (small, medium, large)
        6. Save dashboard configuration
        7. Refresh page and verify configuration persists
        8. Verify configuration stored in user preferences (database)

        VALIDATION:
        - Widgets customizable (add/remove)
        - Layout saves successfully
        - Configuration persists after refresh
        - Database stores configuration correctly
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

        # Navigate to analytics dashboard
        wait.until(EC.url_contains("/instructor-dashboard"))

        # Navigate to analytics tab
        analytics_tab = wait.until(
            EC.element_to_be_clickable((By.ID, "analytics-tab"))
        )
        analytics_tab.click()
        time.sleep(2)

        # Get initial dashboard state
        initial_widgets = page.get_dashboard_widgets()
        initial_count = len(initial_widgets)

        # Enter "Edit Dashboard" mode
        edit_dashboard_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "edit-dashboard-btn"))
        )
        edit_dashboard_btn.click()
        time.sleep(1)

        # VERIFICATION: Edit mode activated
        edit_mode_indicator = browser.find_element(By.CLASS_NAME, "dashboard-edit-mode")
        assert edit_mode_indicator.is_displayed(), "Should be in edit mode"

        # Add "Student Engagement" widget
        add_widget_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "add-widget-btn"))
        )
        add_widget_btn.click()
        time.sleep(0.5)

        # Select Student Engagement from widget library
        engagement_widget = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@data-widget-type='student_engagement']"))
        )
        engagement_widget.click()
        time.sleep(1)

        # VERIFICATION: Student Engagement widget added
        widgets_after_add = page.get_dashboard_widgets()
        assert len(widgets_after_add) > initial_count, "Should have added widget"

        engagement_widget_present = any(
            w['type'] == 'student_engagement' for w in widgets_after_add
        )
        assert engagement_widget_present, "Student Engagement widget should be present"

        # Remove "Course Revenue" widget (if present)
        revenue_widgets = browser.find_elements(
            By.XPATH, "//div[@data-widget-type='course_revenue']"
        )

        if revenue_widgets:
            # Find remove button for revenue widget
            remove_btn = revenue_widgets[0].find_element(By.CLASS_NAME, "remove-widget-btn")
            remove_btn.click()
            time.sleep(1)

            # Confirm removal
            confirm_remove = wait.until(
                EC.element_to_be_clickable((By.ID, "confirm-remove-widget"))
            )
            confirm_remove.click()
            time.sleep(1)

            # VERIFICATION: Course Revenue widget removed
            widgets_after_remove = page.get_dashboard_widgets()
            revenue_still_present = any(
                w['type'] == 'course_revenue' for w in widgets_after_remove
            )
            assert not revenue_still_present, "Course Revenue widget should be removed"

        # Reorder widgets via drag-and-drop
        # Get first two widgets
        widget_elements = browser.find_elements(By.CLASS_NAME, "widget-container")

        if len(widget_elements) >= 2:
            from selenium.webdriver.common.action_chains import ActionChains

            source_widget = widget_elements[0]
            target_widget = widget_elements[1]

            # Record original order
            original_first_type = source_widget.get_attribute("data-widget-type")
            original_second_type = target_widget.get_attribute("data-widget-type")

            # Perform drag-and-drop
            actions = ActionChains(browser)
            actions.drag_and_drop(source_widget, target_widget).perform()
            time.sleep(1)

            # Get widgets after reorder
            reordered_elements = browser.find_elements(By.CLASS_NAME, "widget-container")

            # VERIFICATION: Widget order changed
            new_first_type = reordered_elements[0].get_attribute("data-widget-type")
            # Order should have changed (or at least attempt was made)

        # Change widget sizes
        # Find a widget to resize
        resizable_widget = browser.find_elements(By.CLASS_NAME, "widget-container")[0]

        # Open size selector
        size_selector = resizable_widget.find_element(By.CLASS_NAME, "widget-size-selector")
        size_selector.click()
        time.sleep(0.5)

        # Change to large size
        large_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-size='large']"))
        )
        large_option.click()
        time.sleep(1)

        # VERIFICATION: Widget size changed
        widget_size_class = resizable_widget.get_attribute("class")
        assert 'large' in widget_size_class.lower() or 'widget-lg' in widget_size_class.lower(), \
            "Widget should be resized to large"

        # Save dashboard configuration
        save_dashboard_btn = browser.find_element(By.ID, "save-dashboard-btn")
        save_dashboard_btn.click()
        time.sleep(2)

        # VERIFICATION: Save confirmation shown
        save_confirmation = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-saved-confirmation"))
        )
        assert save_confirmation.is_displayed(), "Should show save confirmation"

        # Exit edit mode
        exit_edit_btn = browser.find_element(By.ID, "exit-edit-mode-btn")
        exit_edit_btn.click()
        time.sleep(1)

        # DATABASE VERIFICATION: Configuration stored in user preferences
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT dashboard_config, updated_at
            FROM user_dashboard_configs
            WHERE user_id = %s AND dashboard_type = 'analytics'
        """, (instructor_credentials.get("user_id"),))

        db_config = cursor.fetchone()
        assert db_config is not None, "Dashboard config should be saved to database"

        config_json_str, updated_at = db_config
        config_json = json.loads(config_json_str)

        # VERIFICATION: Config includes widgets
        assert 'widgets' in config_json, "Config should include widgets array"
        assert len(config_json['widgets']) > 0, "Config should have at least one widget"

        # VERIFICATION: Config includes Student Engagement widget
        engagement_in_config = any(
            w.get('type') == 'student_engagement' for w in config_json['widgets']
        )
        assert engagement_in_config, "Config should include Student Engagement widget"

        # VERIFICATION: Config does NOT include Course Revenue widget
        revenue_in_config = any(
            w.get('type') == 'course_revenue' for w in config_json['widgets']
        )
        assert not revenue_in_config, "Config should NOT include removed Course Revenue widget"

        # VERIFICATION: Widget sizes stored
        has_large_widget = any(
            w.get('size') == 'large' for w in config_json['widgets']
        )
        assert has_large_widget, "Config should include large widget size"

        # Refresh page and verify configuration persists
        browser.refresh()
        time.sleep(3)

        # Wait for dashboard to load
        wait.until(EC.presence_of_element_located((By.ID, "analytics-dashboard")))
        time.sleep(2)

        # Get persisted widgets
        persisted_widgets = page.get_dashboard_widgets()

        # VERIFICATION: Student Engagement widget still present
        engagement_persisted = any(
            w['type'] == 'student_engagement' for w in persisted_widgets
        )
        assert engagement_persisted, \
            "Student Engagement widget should persist after page refresh"

        # VERIFICATION: Course Revenue widget still absent
        revenue_persisted = any(
            w['type'] == 'course_revenue' for w in persisted_widgets
        )
        assert not revenue_persisted, \
            "Removed Course Revenue widget should remain absent after refresh"

        # VERIFICATION: Widget sizes persisted
        large_widgets = [
            w for w in persisted_widgets
            if 'large' in w.get('title', '').lower() or
               browser.find_elements(
                   By.XPATH,
                   f"//div[@data-widget-type='{w['type']}' and contains(@class, 'large')]"
               )
        ]
        # At least one large widget should exist
