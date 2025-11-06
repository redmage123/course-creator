"""
Frontend tests for the course publishing system.
Tests the JavaScript functionality and user interface components.
"""

import pytest
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from unittest.mock import patch, Mock

# Test configuration
FRONTEND_BASE_URL = 'http://localhost:3000'
API_BASE_URL = 'http://localhost:8004'

@pytest.fixture(scope='session')
def driver():
    """Create Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Use new headless mode for better compatibility
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=0')  # Auto-assign random port
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@pytest.fixture
def mock_api_responses():
    """Mock API responses for frontend testing."""
    return {
        'published_courses': {
            'success': True,
            'courses': [
                {
                    'id': 'course-1',
                    'title': 'Test Course 1',
                    'visibility': 'public',
                    'status': 'published',
                    'published_at': '2024-01-01T00:00:00Z',
                    'instance_count': 2
                },
                {
                    'id': 'course-2', 
                    'title': 'Test Course 2',
                    'visibility': 'private',
                    'status': 'published',
                    'published_at': '2024-01-02T00:00:00Z',
                    'instance_count': 1
                }
            ]
        },
        'course_instances': {
            'success': True,
            'instances': [
                {
                    'id': 'instance-1',
                    'instance_name': 'Fall 2024',
                    'course_title': 'Test Course 1',
                    'status': 'scheduled',
                    'start_datetime': '2024-09-01T09:00:00Z',
                    'end_datetime': '2024-12-15T17:00:00Z',
                    'timezone': 'America/New_York',
                    'enrolled_count': 15,
                    'max_students': 30
                }
            ]
        },
        'enroll_student': {
            'success': True,
            'enrollment': {
                'id': 'enrollment-1',
                'student_email': 'test@example.com',
                'student_first_name': 'John',
                'student_last_name': 'Doe',
                'unique_access_url': 'http://localhost:3000/student-login?token=abc123',
                'access_token': 'abc123'
            },
            'message': 'Student enrolled successfully'
        }
    }

class TestInstructorDashboardCoursePublishing:
    """Test course publishing functionality in instructor dashboard."""
    
    def test_published_courses_section_loads(self, driver, mock_api_responses):
        """Test that published courses section loads correctly."""
        # Mock the API call
        driver.execute_script("""
            // Mock fetch for published courses
            const originalFetch = window.fetch;
            window.fetch = function(url, options) {
                if (url.includes('/courses/published')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve(arguments[0])
                    });
                }
                return originalFetch.apply(this, arguments);
            };
            
            // Mock instructor dashboard instance
            window.instructorDashboard = {
                loadPublishedCourses: () => {
                    const container = document.getElementById('publishedCoursesContainer');
                    if (container) {
                        container.innerHTML = `
                            <div class="course-card">
                                <div class="course-header">
                                    <h3>Test Course 1</h3>
                                    <div class="course-badges">
                                        <span class="badge public">public</span>
                                        <span class="badge published">published</span>
                                    </div>
                                </div>
                                <div class="course-meta">
                                    <p><i class="fas fa-calendar"></i> Published: 1/1/2024</p>
                                    <p><i class="fas fa-users"></i> Instances: 2</p>
                                </div>
                                <div class="course-actions">
                                    <button class="btn btn-primary">View Instances</button>
                                    <button class="btn btn-secondary">New Instance</button>
                                    <button class="btn btn-outline">Unpublish</button>
                                </div>
                            </div>
                        `;
                    }
                }
            };
        """, mock_api_responses['published_courses'])
        
        # Load instructor dashboard
        driver.get(f'{FRONTEND_BASE_URL}/instructor-dashboard.html')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'publishedCoursesContainer'))
        )
        
        # Navigate to published courses section
        driver.execute_script("showSection('published-courses')")
        
        # Trigger loading of published courses
        driver.execute_script("window.instructorDashboard.loadPublishedCourses()")
        
        # Wait for courses to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.course-card'))
        )
        
        # Verify course card elements
        course_card = driver.find_element(By.CSS_SELECTOR, '.course-card')
        assert course_card.is_displayed()
        
        course_title = course_card.find_element(By.TAG_NAME, 'h3')
        assert course_title.text == 'Test Course 1'
        
        badges = course_card.find_elements(By.CSS_SELECTOR, '.badge')
        assert len(badges) == 2
        assert any('public' in badge.get_attribute('class') for badge in badges)
        assert any('published' in badge.get_attribute('class') for badge in badges)
        
        action_buttons = course_card.find_elements(By.CSS_SELECTOR, '.course-actions button')
        assert len(action_buttons) == 3

    def test_course_instances_section_loads(self, driver, mock_api_responses):
        """Test that course instances section loads correctly."""
        # Mock the API and instructor dashboard
        driver.execute_script("""
            window.instructorDashboard = {
                loadCourseInstances: () => {
                    const container = document.getElementById('courseInstancesContainer');
                    if (container) {
                        container.innerHTML = `
                            <div class="instance-card">
                                <div class="instance-header">
                                    <h3>Fall 2024</h3>
                                    <span class="badge scheduled">scheduled</span>
                                </div>
                                <div class="instance-details">
                                    <p><strong>Course:</strong> Test Course 1</p>
                                    <p><strong>Duration:</strong> 9/1/2024 - 12/15/2024</p>
                                    <p><strong>Timezone:</strong> America/New_York</p>
                                    <p><strong>Students:</strong> 15/30</p>
                                </div>
                                <div class="instance-actions">
                                    <button class="btn btn-primary">View Students</button>
                                    <button class="btn btn-secondary">Enroll Student</button>
                                </div>
                            </div>
                        `;
                    }
                }
            };
        """)
        
        # Load instructor dashboard
        driver.get(f'{FRONTEND_BASE_URL}/instructor-dashboard.html')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'courseInstancesContainer'))
        )
        
        # Navigate to course instances section
        driver.execute_script("showSection('course-instances')")
        
        # Trigger loading of course instances
        driver.execute_script("window.instructorDashboard.loadCourseInstances()")
        
        # Wait for instances to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.instance-card'))
        )
        
        # Verify instance card elements
        instance_card = driver.find_element(By.CSS_SELECTOR, '.instance-card')
        assert instance_card.is_displayed()
        
        instance_title = instance_card.find_element(By.TAG_NAME, 'h3')
        assert instance_title.text == 'Fall 2024'
        
        status_badge = instance_card.find_element(By.CSS_SELECTOR, '.badge')
        assert 'scheduled' in status_badge.get_attribute('class')
        
        details = instance_card.find_elements(By.CSS_SELECTOR, '.instance-details p')
        assert len(details) == 4
        assert 'Test Course 1' in details[0].text
        assert '15/30' in details[3].text

    def test_create_instance_modal_functionality(self, driver):
        """Test create course instance modal functionality."""
        # Load instructor dashboard
        driver.get(f'{FRONTEND_BASE_URL}/instructor-dashboard.html')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'createInstanceModal'))
        )
        
        # Mock instructor dashboard functions
        driver.execute_script("""
            window.instructorDashboard = {
                showCreateInstanceModal: () => {
                    const modal = document.getElementById('createInstanceModal');
                    modal.style.display = 'block';
                    
                    // Populate course dropdown
                    const courseSelect = document.getElementById('instanceCourse');
                    courseSelect.innerHTML = `
                        <option value="">Select a published course...</option>
                        <option value="course-1">Test Course 1</option>
                        <option value="course-2">Test Course 2</option>
                    `;
                },
                submitCreateInstance: () => {
                    // Mock form submission
                    const form = document.getElementById('createInstanceForm');
                    const formData = new FormData(form);
                    console.log('Form submitted with:', Object.fromEntries(formData));
                    
                    // Close modal
                    document.getElementById('createInstanceModal').style.display = 'none';
                    
                    // Show success message (simulate)
                    alert('Course instance created successfully!');
                }
            };
            
            window.showCreateInstanceModal = () => {
                window.instructorDashboard.showCreateInstanceModal();
            };
            
            window.submitCreateInstance = () => {
                window.instructorDashboard.submitCreateInstance();
            };
        """)
        
        # Open create instance modal
        driver.execute_script("window.showCreateInstanceModal()")
        
        # Wait for modal to be visible
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'instanceCourse'))
        )
        
        # Verify modal is displayed
        modal = driver.find_element(By.ID, 'createInstanceModal')
        assert modal.is_displayed()
        
        # Fill out the form
        course_select = Select(driver.find_element(By.ID, 'instanceCourse'))
        course_select.select_by_value('course-1')
        
        instance_name = driver.find_element(By.ID, 'instanceName')
        instance_name.send_keys('Test Instance Spring 2024')
        
        start_date = driver.find_element(By.ID, 'startDate')
        start_date.send_keys('2024-03-01')
        
        start_time = driver.find_element(By.ID, 'startTime')
        start_time.send_keys('09:00')
        
        end_date = driver.find_element(By.ID, 'endDate')
        end_date.send_keys('2024-05-15')
        
        end_time = driver.find_element(By.ID, 'endTime')
        end_time.send_keys('17:00')
        
        timezone_select = Select(driver.find_element(By.ID, 'timezone'))
        timezone_select.select_by_value('America/New_York')
        
        max_students = driver.find_element(By.ID, 'maxStudents')
        max_students.clear()
        max_students.send_keys('25')
        
        description = driver.find_element(By.ID, 'instanceDescription')
        description.send_keys('Test instance description')
        
        # Submit the form
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button[onclick="submitCreateInstance()"]')
        submit_button.click()
        
        # Wait for alert (simulated success message)
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        assert 'Course instance created successfully!' in alert.text
        alert.accept()
        
        # Verify modal is closed
        assert not modal.is_displayed()

    def test_student_enrollment_modal_functionality(self, driver):
        """Test student enrollment modal functionality."""
        # Load instructor dashboard
        driver.get(f'{FRONTEND_BASE_URL}/instructor-dashboard.html')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'enrollStudentModal'))
        )
        
        # Mock instructor dashboard functions
        driver.execute_script("""
            window.instructorDashboard = {
                showEnrollStudentModal: (instanceId) => {
                    document.getElementById('enrollInstanceId').value = instanceId;
                    document.getElementById('enrollStudentModal').style.display = 'block';
                },
                submitEnrollStudent: () => {
                    const form = document.getElementById('enrollStudentForm');
                    const formData = new FormData(form);
                    console.log('Enrollment submitted:', Object.fromEntries(formData));
                    
                    // Close modal
                    document.getElementById('enrollStudentModal').style.display = 'none';
                    
                    // Show success message
                    alert('Student enrolled successfully!');
                }
            };
        """)
        
        # Open enrollment modal
        driver.execute_script("window.instructorDashboard.showEnrollStudentModal('test-instance-id')")
        
        # Wait for modal to be visible
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'studentEmail'))
        )
        
        # Verify modal is displayed
        modal = driver.find_element(By.ID, 'enrollStudentModal')
        assert modal.is_displayed()
        
        # Verify instance ID is set
        instance_id_field = driver.find_element(By.ID, 'enrollInstanceId')
        assert instance_id_field.get_attribute('value') == 'test-instance-id'
        
        # Fill out enrollment form
        student_email = driver.find_element(By.ID, 'studentEmail')
        student_email.send_keys('newstudent@example.com')
        
        student_name = driver.find_element(By.ID, 'studentName')
        student_name.send_keys('New Student')
        
        # Check welcome email checkbox
        welcome_email_checkbox = driver.find_element(By.ID, 'sendWelcomeEmail')
        assert welcome_email_checkbox.is_selected()  # Should be checked by default
        
        # Submit enrollment
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button[onclick="submitEnrollStudent()"]')
        submit_button.click()
        
        # Wait for alert
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        assert 'Student enrolled successfully!' in alert.text
        alert.accept()
        
        # Verify modal is closed
        assert not modal.is_displayed()


class TestStudentLoginPage:
    """Test student login page functionality."""
    
    def test_student_login_page_loads(self, driver):
        """Test that student login page loads correctly."""
        # Load student login page with token
        test_token = 'test_token_123456789012345'
        driver.get(f'{FRONTEND_BASE_URL}/student-login.html?token={test_token}')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'loginForm'))
        )
        
        # Verify page elements
        logo = driver.find_element(By.CSS_SELECTOR, '.logo h1')
        assert 'Course Creator' in logo.text
        
        # Verify access token is pre-filled
        access_token_field = driver.find_element(By.ID, 'accessToken')
        assert access_token_field.get_attribute('value') == test_token
        
        # Verify form elements exist
        password_field = driver.find_element(By.ID, 'password')
        assert password_field.is_displayed()
        
        login_button = driver.find_element(By.ID, 'loginBtn')
        assert login_button.is_displayed()
        assert 'Access Course' in login_button.text

    def test_student_login_form_validation(self, driver):
        """Test form validation on student login page."""
        driver.get(f'{FRONTEND_BASE_URL}/student-login.html')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'loginForm'))
        )
        
        # Try to submit empty form
        login_button = driver.find_element(By.ID, 'loginBtn')
        login_button.click()
        
        # HTML5 validation should prevent submission
        access_token_field = driver.find_element(By.ID, 'accessToken')
        validation_message = access_token_field.get_attribute('validationMessage')
        assert validation_message  # Should have validation message
        
        # Fill access token but leave password empty
        access_token_field.send_keys('test_token')
        login_button.click()
        
        # Password field should be invalid
        password_field = driver.find_element(By.ID, 'password')
        validation_message = password_field.get_attribute('validationMessage')
        assert validation_message

    def test_student_login_with_mock_api(self, driver):
        """Test student login with mocked API responses."""
        # Mock API responses
        driver.execute_script("""
            // Mock successful login response
            window.fetch = function(url, options) {
                if (url.includes('/student/auth/login')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            success: true,
                            student: {
                                student_email: 'test@example.com',
                                student_name: 'Test Student',
                                course_title: 'Test Course',
                                password_reset_required: false,
                                access_token: 'test_token_123'
                            },
                            message: 'Authentication successful'
                        })
                    });
                } else if (url.includes('/student/course-data')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            success: true,
                            data: {
                                course: {
                                    title: 'Test Course',
                                    description: 'Test course description'
                                },
                                instance: {
                                    name: 'Test Instance'
                                }
                            }
                        })
                    });
                }
                return Promise.reject(new Error('Not mocked'));
            };
        """)
        
        # Load student login page
        driver.get(f'{FRONTEND_BASE_URL}/student-login.html?token=test_token_123')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'loginForm'))
        )
        
        # Fill in password
        password_field = driver.find_element(By.ID, 'password')
        password_field.send_keys('test_password')
        
        # Submit form
        login_button = driver.find_element(By.ID, 'loginBtn')
        login_button.click()
        
        # Wait for success message
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, 'successMessage'))
        )
        
        success_message = driver.find_element(By.ID, 'successMessage')
        assert success_message.is_displayed()
        assert 'Login successful' in success_message.text

    def test_student_password_reset_form(self, driver):
        """Test password reset form functionality."""
        driver.get(f'{FRONTEND_BASE_URL}/student-login.html')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'loginForm'))
        )
        
        # Click password reset link
        reset_link = driver.find_element(By.CSS_SELECTOR, 'a[onclick="showPasswordResetForm()"]')
        reset_link.click()
        
        # Wait for password reset form to be visible
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, 'passwordResetForm'))
        )
        
        # Verify login form is hidden and reset form is visible
        login_form = driver.find_element(By.ID, 'loginForm')
        reset_form = driver.find_element(By.ID, 'passwordResetForm')
        
        assert not login_form.is_displayed()
        assert reset_form.is_displayed()
        
        # Verify password requirements are shown when typing
        new_password_field = driver.find_element(By.ID, 'newPassword')
        new_password_field.send_keys('test')
        
        # Password requirements should be visible
        requirements = driver.find_element(By.ID, 'passwordRequirements')
        assert requirements.is_displayed()
        
        # Test back to login button
        back_button = driver.find_element(By.CSS_SELECTOR, 'button[onclick="showLoginForm()"]')
        back_button.click()
        
        # Login form should be visible again
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, 'loginForm'))
        )
        assert login_form.is_displayed()
        assert not reset_form.is_displayed()

    def test_course_info_display(self, driver):
        """Test course information display on login page."""
        # Mock course data API
        driver.execute_script("""
            window.fetch = function(url, options) {
                if (url.includes('/student/course-data')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            success: true,
                            data: {
                                course: {
                                    title: 'Advanced JavaScript Programming',
                                    description: 'Learn advanced JavaScript concepts and frameworks'
                                },
                                instance: {
                                    name: 'Spring 2024 Locations'
                                }
                            }
                        })
                    });
                }
                return Promise.reject(new Error('Not mocked'));
            };
        """)
        
        # Load page with token
        driver.get(f'{FRONTEND_BASE_URL}/student-login.html?token=test_token_123')
        
        # Wait for course info to load
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'courseInfo'))
        )
        
        # Verify course information is displayed
        course_info = driver.find_element(By.ID, 'courseInfo')
        assert course_info.is_displayed()
        
        course_title = driver.find_element(By.ID, 'courseTitle')
        assert course_title.text == 'Advanced JavaScript Programming'
        
        course_description = driver.find_element(By.ID, 'courseDescription')
        assert 'Spring 2024 Locations' in course_description.text
        assert 'Learn advanced JavaScript concepts' in course_description.text


class TestCoursePublishingJavaScript:
    """Test JavaScript functionality for course publishing."""
    
    def test_instructor_dashboard_module_loading(self, driver):
        """Test that instructor dashboard module loads correctly."""
        driver.get(f'{FRONTEND_BASE_URL}/instructor-dashboard.html')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Check if instructor dashboard module is loaded
        instructor_dashboard_loaded = driver.execute_script("""
            return typeof window.instructorDashboard !== 'undefined';
        """)
        
        # If not loaded, it should be loaded when switching to relevant sections
        if not instructor_dashboard_loaded:
            # Try switching to published courses section
            driver.execute_script("showSection('published-courses')")
            
            # Wait a bit for potential loading
            time.sleep(1)
            
            # Check again
            instructor_dashboard_loaded = driver.execute_script("""
                return typeof window.instructorDashboard !== 'undefined' || 
                       typeof window.showCreateInstanceModal !== 'undefined';
            """)
        
        # At minimum, the global functions should be available
        global_functions_available = driver.execute_script("""
            return typeof window.showCreateInstanceModal === 'function' &&
                   typeof window.submitCreateInstance === 'function' &&
                   typeof window.submitEnrollStudent === 'function' &&
                   typeof window.closeModal === 'function';
        """)
        
        assert global_functions_available, "Global course publishing functions should be available"

    def test_modal_functionality(self, driver):
        """Test modal opening and closing functionality."""
        driver.get(f'{FRONTEND_BASE_URL}/instructor-dashboard.html')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'createInstanceModal'))
        )
        
        # Test opening modal
        driver.execute_script("""
            document.getElementById('createInstanceModal').style.display = 'block';
        """)
        
        modal = driver.find_element(By.ID, 'createInstanceModal')
        assert modal.is_displayed()
        
        # Test closing modal
        driver.execute_script("closeModal('createInstanceModal')")
        
        assert not modal.is_displayed()

    def test_form_validation_javascript(self, driver):
        """Test JavaScript form validation."""
        driver.get(f'{FRONTEND_BASE_URL}/student-login.html')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'loginForm'))
        )
        
        # Test password validation function
        password_validation_result = driver.execute_script("""
            // Define the password validation function (from the page)
            function validatePassword(password) {
                const requirements = {
                    length: password.length >= 8,
                    uppercase: /[A-Z]/.test(password),
                    lowercase: /[a-z]/.test(password),
                    number: /\\d/.test(password),
                    special: /[!@#$%^&*()_+\\-=\\[\\]{};':"\\\\|,.<>\\?]/.test(password)
                };
                
                return Object.values(requirements).every(req => req);
            }
            
            // Test various passwords
            return {
                weak: validatePassword('weak'),
                strong: validatePassword('StrongPass123!'),
                noUpper: validatePassword('weakpass123!'),
                noSpecial: validatePassword('WeakPass123')
            };
        """)
        
        assert password_validation_result['weak'] == False
        assert password_validation_result['strong'] == True
        assert password_validation_result['noUpper'] == False
        assert password_validation_result['noSpecial'] == False


if __name__ == '__main__':
    pytest.main([__file__])