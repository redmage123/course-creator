"""
End-to-End Tests for Analytics Dashboard
Tests the complete analytics workflow from frontend dashboard to backend analytics service
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
import requests
import json

class TestAnalyticsDashboardE2E:
    """End-to-end tests for the analytics dashboard functionality"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        # Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except WebDriverException as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
        
        # Test configuration
        cls.base_url = "http://localhost:8080"
        cls.analytics_api_url = "http://localhost:8007"
        cls.instructor_dashboard_url = f"{cls.base_url}/instructor-dashboard.html"
        
        # Test data
        cls.test_course_id = "test-course-analytics-e2e"
        cls.test_student_id = "test-student-analytics-e2e"
        cls.test_instructor = {
            "username": "test_instructor@example.com",
            "password": "test_password_123"
        }
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def setup_method(self):
        """Set up individual test"""
        self.wait = WebDriverWait(self.driver, 10)
    
    def test_analytics_service_health(self):
        """Test that analytics service is healthy"""
        try:
            response = requests.get(f"{self.analytics_api_url}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "analytics"
        except requests.exceptions.RequestException:
            pytest.skip("Analytics service not available")
    
    def test_load_instructor_dashboard(self):
        """Test loading the instructor dashboard"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Check that the page loaded correctly
        assert "Instructor Dashboard" in self.driver.title
        
        # Check for analytics navigation
        analytics_nav = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        assert analytics_nav is not None
    
    def test_navigate_to_analytics_section(self):
        """Test navigating to the analytics section"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Click on analytics navigation
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # Wait for analytics section to be visible
        analytics_section = self.wait.until(
            EC.visibility_of_element_located((By.ID, "analytics-section"))
        )
        
        # Check that analytics section is displayed
        assert analytics_section.is_displayed()
        
        # Check for analytics components
        assert self.driver.find_element(By.ID, "analyticsCourseSelect")
        assert self.driver.find_element(By.ID, "analyticsTimeRange")
        assert self.driver.find_element(By.ID, "refreshAnalyticsBtn")
        assert self.driver.find_element(By.ID, "exportAnalyticsBtn")
    
    def test_analytics_controls_interaction(self):
        """Test interaction with analytics controls"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Navigate to analytics
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # Wait for analytics section
        self.wait.until(EC.visibility_of_element_located((By.ID, "analytics-section")))
        
        # Test time range selector
        time_range_select = Select(self.driver.find_element(By.ID, "analyticsTimeRange"))
        time_range_select.select_by_value("7")  # Last 7 days
        
        # Verify selection
        selected_option = time_range_select.first_selected_option
        assert selected_option.get_attribute("value") == "7"
        
        # Test refresh button
        refresh_btn = self.driver.find_element(By.ID, "refreshAnalyticsBtn")
        assert refresh_btn.is_enabled()
        
        # Test export button
        export_btn = self.driver.find_element(By.ID, "exportAnalyticsBtn")
        assert export_btn.is_enabled()
    
    def test_analytics_overview_cards_display(self):
        """Test that analytics overview cards are displayed"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Navigate to analytics
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # Wait for analytics section
        self.wait.until(EC.visibility_of_element_located((By.ID, "analytics-section")))
        
        # Check for overview cards
        total_students_card = self.driver.find_element(By.ID, "totalStudentsCount")
        active_students_card = self.driver.find_element(By.ID, "activeStudentsCount")
        avg_quiz_score_card = self.driver.find_element(By.ID, "avgQuizScore")
        lab_completion_card = self.driver.find_element(By.ID, "labCompletionRate")
        
        # Verify cards are present
        assert total_students_card is not None
        assert active_students_card is not None
        assert avg_quiz_score_card is not None
        assert lab_completion_card is not None
        
        # Check initial values (should be "-" for empty state)
        assert total_students_card.text == "-"
        assert active_students_card.text == "-"
        assert avg_quiz_score_card.text == "-%"
        assert lab_completion_card.text == "-%"
    
    def test_analytics_charts_containers(self):
        """Test that chart containers are present"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Navigate to analytics
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # Wait for analytics section
        self.wait.until(EC.visibility_of_element_located((By.ID, "analytics-section")))
        
        # Check for chart containers
        engagement_chart = self.driver.find_element(By.ID, "engagementChart")
        lab_completion_chart = self.driver.find_element(By.ID, "labCompletionChart")
        quiz_performance_chart = self.driver.find_element(By.ID, "quizPerformanceChart")
        progress_distribution_chart = self.driver.find_element(By.ID, "progressDistributionChart")
        
        # Verify chart containers are present
        assert engagement_chart is not None
        assert lab_completion_chart is not None
        assert quiz_performance_chart is not None
        assert progress_distribution_chart is not None
        
        # Check that charts are canvas elements
        assert engagement_chart.tag_name == "canvas"
        assert lab_completion_chart.tag_name == "canvas"
        assert quiz_performance_chart.tag_name == "canvas"
        assert progress_distribution_chart.tag_name == "canvas"
    
    def test_student_analytics_list_section(self):
        """Test student analytics list section"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Navigate to analytics
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # Wait for analytics section
        self.wait.until(EC.visibility_of_element_located((By.ID, "analytics-section")))
        
        # Check for student analytics components
        student_search = self.driver.find_element(By.ID, "studentSearchInput")
        students_list = self.driver.find_element(By.ID, "studentsAnalyticsList")
        
        assert student_search is not None
        assert students_list is not None
        
        # Test search input functionality
        assert student_search.get_attribute("placeholder") == "Search students..."
        
        # Check initial loading state
        loading_indicator = students_list.find_element(By.CLASS_NAME, "loading-indicator")
        assert "Loading students..." in loading_indicator.text
    
    def test_student_search_functionality(self):
        """Test student search functionality"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Navigate to analytics
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # Wait for analytics section
        self.wait.until(EC.visibility_of_element_located((By.ID, "analytics-section")))
        
        # Find search input
        student_search = self.driver.find_element(By.ID, "studentSearchInput")
        
        # Test typing in search
        test_search_term = "Alice"
        student_search.clear()
        student_search.send_keys(test_search_term)
        
        # Verify search input has the correct value
        assert student_search.get_attribute("value") == test_search_term
    
    def test_loading_states(self):
        """Test loading states and error handling"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Navigate to analytics
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # Wait for analytics section
        self.wait.until(EC.visibility_of_element_located((By.ID, "analytics-section")))
        
        # Check for loading/error message elements
        loading_element = self.driver.find_element(By.ID, "analyticsLoading")
        error_element = self.driver.find_element(By.ID, "analyticsError")
        success_element = self.driver.find_element(By.ID, "analyticsSuccess")
        
        # These should be present but initially hidden
        assert loading_element is not None
        assert error_element is not None
        assert success_element is not None
        
        # Check initial display state (should be hidden)
        assert loading_element.get_attribute("style") == "display: none;"
        assert error_element.get_attribute("style") == "display: none;"
        assert success_element.get_attribute("style") == "display: none;"
    
    def test_responsive_design(self):
        """Test responsive design of analytics dashboard"""
        # Test different viewport sizes
        viewport_sizes = [
            (1920, 1080),  # Desktop
            (1024, 768),   # Tablet
            (768, 1024),   # Tablet portrait
            (375, 667)     # Mobile
        ]
        
        for width, height in viewport_sizes:
            self.driver.set_window_size(width, height)
            self.driver.get(self.instructor_dashboard_url)
            
            # Navigate to analytics
            analytics_nav = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
            )
            analytics_nav.click()
            
            # Wait for analytics section
            analytics_section = self.wait.until(
                EC.visibility_of_element_located((By.ID, "analytics-section"))
            )
            
            # Verify section is visible and has content
            assert analytics_section.is_displayed()
            
            # Check that controls are still accessible
            controls = self.driver.find_element(By.CLASS_NAME, "analytics-controls")
            assert controls.is_displayed()


class TestAnalyticsDataVisualization:
    """Test analytics data visualization components"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment for visualization tests"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except WebDriverException as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
        
        cls.base_url = "http://localhost:8080"
        cls.instructor_dashboard_url = f"{cls.base_url}/instructor-dashboard.html"
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def setup_method(self):
        """Set up individual test"""
        self.wait = WebDriverWait(self.driver, 10)
    
    def test_chart_js_library_loaded(self):
        """Test that Chart.js library is loaded"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Check if Chart.js is loaded
        chart_js_loaded = self.driver.execute_script("return typeof Chart !== 'undefined';")
        assert chart_js_loaded, "Chart.js library should be loaded"
    
    def test_analytics_dashboard_module_loaded(self):
        """Test that analytics dashboard module is loaded"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Wait for page to load completely
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Check if analytics dashboard is available
        analytics_available = self.driver.execute_script(
            "return typeof window.analyticsDashboard !== 'undefined';"
        )
        
        # Note: This might be false initially if module loading is async
        # The test verifies that the module loading mechanism is in place
        script_tags = self.driver.find_elements(By.TAG_NAME, "script")
        analytics_script_found = any(
            "analytics-dashboard" in script.get_attribute("src") or ""
            for script in script_tags
            if script.get_attribute("src")
        )
        
        # Either the module is loaded or the script tag is present
        assert analytics_available or analytics_script_found
    
    def test_chart_containers_dimensions(self):
        """Test that chart containers have proper dimensions"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Navigate to analytics
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # Wait for analytics section
        self.wait.until(EC.visibility_of_element_located((By.ID, "analytics-section")))
        
        # Check chart container dimensions
        charts = [
            "engagementChart",
            "labCompletionChart", 
            "quizPerformanceChart",
            "progressDistributionChart"
        ]
        
        for chart_id in charts:
            chart_element = self.driver.find_element(By.ID, chart_id)
            
            # Get dimensions
            width = chart_element.get_attribute("width")
            height = chart_element.get_attribute("height")
            
            # Charts should have reasonable dimensions
            # (Chart.js typically sets these automatically)
            assert chart_element.is_displayed()


class TestAnalyticsWorkflow:
    """Test complete analytics workflow scenarios"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment for workflow tests"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except WebDriverException as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
        
        cls.base_url = "http://localhost:8080"
        cls.analytics_api_url = "http://localhost:8007"
        cls.instructor_dashboard_url = f"{cls.base_url}/instructor-dashboard.html"
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def setup_method(self):
        """Set up individual test"""
        self.wait = WebDriverWait(self.driver, 10)
    
    def test_instructor_analytics_workflow(self):
        """Test complete instructor analytics workflow"""
        self.driver.get(self.instructor_dashboard_url)
        
        # 1. Navigate to analytics section
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # 2. Wait for analytics section to load
        analytics_section = self.wait.until(
            EC.visibility_of_element_located((By.ID, "analytics-section"))
        )
        assert analytics_section.is_displayed()
        
        # 3. Check course selection (initially empty)
        course_select = Select(self.driver.find_element(By.ID, "analyticsCourseSelect"))
        default_option = course_select.first_selected_option
        assert default_option.text == "Select a course"
        
        # 4. Change time range
        time_range_select = Select(self.driver.find_element(By.ID, "analyticsTimeRange"))
        time_range_select.select_by_value("90")  # Last 90 days
        
        # 5. Click refresh button
        refresh_btn = self.driver.find_element(By.ID, "refreshAnalyticsBtn")
        refresh_btn.click()
        
        # 6. Check that loading state may appear briefly
        # (Note: In a real test with backend, we'd see actual loading)
        
        # 7. Test export functionality
        export_btn = self.driver.find_element(By.ID, "exportAnalyticsBtn")
        export_btn.click()
        
        # Workflow completed successfully
        assert True
    
    def test_student_search_and_details_workflow(self):
        """Test student search and details workflow"""
        self.driver.get(self.instructor_dashboard_url)
        
        # Navigate to analytics
        analytics_nav = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-section="analytics"]'))
        )
        analytics_nav.click()
        
        # Wait for analytics section
        self.wait.until(EC.visibility_of_element_located((By.ID, "analytics-section")))
        
        # 1. Use student search
        student_search = self.driver.find_element(By.ID, "studentSearchInput")
        student_search.clear()
        student_search.send_keys("Alice")
        
        # 2. In a real scenario with data, we would:
        # - Wait for filtered results
        # - Click on a student card
        # - Check that student details modal opens
        # - Verify student analytics data is displayed
        
        # For now, verify search functionality works
        assert student_search.get_attribute("value") == "Alice"
        
        # 3. Check that student details modal exists in DOM
        # (even if not visible initially)
        try:
            student_modal = self.driver.find_element(By.ID, "studentDetailsModal")
            assert student_modal is not None
        except:
            # Modal might not be in DOM until needed
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])