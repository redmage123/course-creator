"""
E2E Test: Organization Admin Course Generation and Editing

BUSINESS REQUIREMENT:
Organization admins must be able to generate courses using AI and manually edit
the AI-generated content. This includes both org admins and instructors having
the capability to create and modify course materials.

TEST COVERAGE:
1. Org admin can access course generation interface
2. Org admin can generate course using AI
3. Org admin can view AI-generated course content
4. Org admin can manually edit AI-generated syllabus
5. Org admin can save edited course content
6. Instructor can also perform same operations (existing functionality)

RBAC PERMISSIONS:
- organization_admin: Has 'create_courses' permission
- instructor: Has 'create_courses' permission

This test follows TDD RED-GREEN-REFACTOR cycle.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@pytest.fixture
def selenium_driver():
    """Selenium WebDriver fixture with Chrome"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--ignore-certificate-errors")

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)

    yield driver

    driver.quit()


@pytest.fixture
def org_admin_auth(selenium_driver):
    """Authenticate as organization admin"""
    driver = selenium_driver

    # Navigate to home page first
    driver.get("https://localhost:3000/html/index.html")
    time.sleep(2)

    # Set up organization admin authenticated state using localStorage
    driver.execute_script("""
        localStorage.setItem('authToken', 'test-org-admin-token-course-gen');
        localStorage.setItem('currentUser', JSON.stringify({
            id: 100,
            email: 'orgadmin@testorg.com',
            role: 'organization_admin',
            organization_id: 1,
            name: 'Test Org Admin'
        }));
        localStorage.setItem('userEmail', 'orgadmin@testorg.com');
        localStorage.setItem('sessionStart', Date.now().toString());
        localStorage.setItem('lastActivity', Date.now().toString());
    """)

    # Navigate to org admin dashboard
    driver.get("https://localhost:3000/html/org-admin-dashboard.html?org_id=1")
    time.sleep(3)

    return driver


class TestOrgAdminCourseGeneration:
    """Test suite for organization admin course generation and editing"""

    def test_org_admin_can_access_course_generation_tab(self, org_admin_auth, selenium_driver):
        """
        RED: Org admin dashboard should have a 'Courses' tab

        This test will FAIL initially because the Courses tab doesn't exist yet.
        """
        driver = org_admin_auth
        wait = WebDriverWait(driver, 10)

        # Look for Courses tab in sidebar
        courses_tab = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-tab='courses']"))
        )

        assert courses_tab is not None, "Courses tab should exist in org admin dashboard"
        assert courses_tab.is_displayed(), "Courses tab should be visible"

    def test_org_admin_can_click_courses_tab(self, org_admin_auth, selenium_driver):
        """
        RED: Clicking Courses tab should display course management interface

        This test will FAIL because the tab and content don't exist yet.
        """
        driver = org_admin_auth
        wait = WebDriverWait(driver, 10)

        # Click Courses tab
        courses_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tab='courses']"))
        )
        courses_tab.click()

        # Wait for courses content to display
        courses_content = wait.until(
            EC.visibility_of_element_located((By.ID, "courses"))
        )

        assert courses_content.is_displayed(), "Courses content should be visible"

    def test_org_admin_can_see_generate_course_button(self, org_admin_auth, selenium_driver):
        """
        RED: Courses tab should have a 'Generate Course with AI' button

        This test will FAIL because the button doesn't exist yet.
        """
        driver = org_admin_auth
        wait = WebDriverWait(driver, 10)

        # Navigate to Courses tab
        courses_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tab='courses']"))
        )
        courses_tab.click()

        # Look for Generate Course button
        generate_btn = wait.until(
            EC.presence_of_element_located((By.ID, "generateCourseBtn"))
        )

        assert generate_btn is not None, "Generate Course button should exist"
        assert generate_btn.text == "🤖 Generate Course with AI", "Button should have correct text"

    def test_org_admin_can_generate_course_with_ai(self, org_admin_auth, selenium_driver):
        """
        RED: Org admin should be able to generate a course using AI

        This test will FAIL because the course generation flow doesn't exist yet.
        """
        driver = org_admin_auth
        wait = WebDriverWait(driver, 15)

        # Navigate to Courses tab
        courses_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tab='courses']"))
        )
        courses_tab.click()

        # Click Generate Course button
        generate_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "generateCourseBtn"))
        )
        generate_btn.click()

        # Fill in course generation form
        course_title = wait.until(
            EC.presence_of_element_located((By.ID, "generateCourseTitle"))
        )
        course_title.send_keys("Introduction to Python Programming")

        course_description = driver.find_element(By.ID, "generateCourseDescription")
        course_description.send_keys(
            "A comprehensive course for beginners learning Python programming, "
            "covering variables, data types, control flow, functions, and OOP."
        )

        # Select category
        category_select = driver.find_element(By.ID, "generateCourseCategory")
        category_select.send_keys("Programming")

        # Select difficulty
        difficulty_select = driver.find_element(By.ID, "generateCourseDifficulty")
        difficulty_select.send_keys("beginner")

        # Click Generate button
        submit_generate_btn = driver.find_element(By.ID, "submitGenerateCourse")
        submit_generate_btn.click()

        # Wait for AI generation to complete
        success_message = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "generation-success"))
        )

        assert "Course generated successfully" in success_message.text

    def test_org_admin_can_view_generated_course_content(self, org_admin_auth, selenium_driver):
        """
        RED: After generation, org admin should see the AI-generated course content

        This test will FAIL because the course viewing interface doesn't exist yet.
        """
        driver = org_admin_auth
        wait = WebDriverWait(driver, 10)

        # Assuming course was just generated (in real test, we'd set up state)
        # Navigate to course view
        driver.get("https://localhost:3000/html/org-admin-dashboard.html#courses")

        # Click on first course in list
        first_course = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".course-card:first-child"))
        )
        first_course.click()

        # Verify course details modal opens
        course_modal = wait.until(
            EC.visibility_of_element_located((By.ID, "courseDetailsModal"))
        )

        # Check for syllabus content
        syllabus_section = driver.find_element(By.ID, "courseSyllabusContent")
        assert syllabus_section is not None, "Syllabus content should be visible"

        # Check for modules
        modules = driver.find_elements(By.CLASS_NAME, "course-module")
        assert len(modules) > 0, "Generated course should have modules"

    def test_org_admin_can_edit_ai_generated_syllabus(self, org_admin_auth, selenium_driver):
        """
        RED: Org admin should be able to manually edit AI-generated syllabus

        This test will FAIL because the editing interface doesn't exist yet.
        """
        driver = org_admin_auth
        wait = WebDriverWait(driver, 10)

        # Navigate to course and open details
        driver.get("https://localhost:3000/html/org-admin-dashboard.html#courses")

        first_course = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".course-card:first-child"))
        )
        first_course.click()

        # Click Edit Syllabus button
        edit_syllabus_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "editSyllabusBtn"))
        )
        edit_syllabus_btn.click()

        # Verify edit modal opens
        edit_modal = wait.until(
            EC.visibility_of_element_located((By.ID, "editSyllabusModal"))
        )

        # Edit course title
        title_input = driver.find_element(By.ID, "editSyllabusTitle")
        title_input.clear()
        title_input.send_keys("Python Programming - Beginner to Intermediate")

        # Edit module 1 title
        module1_title = driver.find_element(By.ID, "editModule1Title")
        module1_title.clear()
        module1_title.send_keys("Python Basics and Setup")

        # Save changes
        save_btn = driver.find_element(By.ID, "saveSyllabusEditsBtn")
        save_btn.click()

        # Verify success message
        success_msg = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "save-success"))
        )

        assert "Syllabus updated successfully" in success_msg.text

    def test_org_admin_can_save_edited_course(self, org_admin_auth, selenium_driver):
        """
        RED: Edited course should be persisted to database

        This test will FAIL because the save functionality doesn't exist yet.
        """
        driver = org_admin_auth
        wait = WebDriverWait(driver, 10)

        # Navigate to courses
        driver.get("https://localhost:3000/html/org-admin-dashboard.html#courses")

        # Open first course
        first_course = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".course-card:first-child"))
        )
        original_title = first_course.find_element(By.CLASS_NAME, "course-title").text
        first_course.click()

        # Edit and save
        edit_btn = wait.until(EC.element_to_be_clickable((By.ID, "editSyllabusBtn")))
        edit_btn.click()

        title_input = wait.until(EC.presence_of_element_located((By.ID, "editSyllabusTitle")))
        new_title = "Updated: " + original_title
        title_input.clear()
        title_input.send_keys(new_title)

        save_btn = driver.find_element(By.ID, "saveSyllabusEditsBtn")
        save_btn.click()

        # Wait for save to complete
        time.sleep(1)

        # Close modal
        close_btn = driver.find_element(By.CLASS_NAME, "close-modal")
        close_btn.click()

        # Refresh page
        driver.refresh()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".course-card")))

        # Verify title persisted
        first_course_after_refresh = driver.find_element(By.CSS_SELECTOR, ".course-card:first-child")
        updated_title_element = first_course_after_refresh.find_element(By.CLASS_NAME, "course-title")

        assert updated_title_element.text == new_title, "Course title should persist after refresh"


class TestInstructorCourseGenerationEquivalence:
    """
    Verify that instructors have the same course generation/editing capabilities.
    This should already work, but we're testing to ensure equivalence.
    """

    @pytest.fixture
    def instructor_auth(self, selenium_driver):
        """Authenticate as instructor"""
        driver = selenium_driver
        wait = WebDriverWait(driver, 10)

        # Navigate and login
        driver.get("https://localhost:3000/html/index.html")

        login_btn = wait.until(EC.element_to_be_clickable((By.ID, "loginBtn")))
        login_btn.click()

        email_field = wait.until(EC.presence_of_element_located((By.ID, "loginEmail")))
        email_field.send_keys("instructor@example.com")

        password_field = driver.find_element(By.ID, "loginPassword")
        password_field.send_keys("instructor_password")

        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # Wait for instructor dashboard
        wait.until(EC.url_contains("instructor-dashboard"))

        return driver

    def test_instructor_has_course_generation_capability(self, instructor_auth, selenium_driver):
        """
        GREEN: This should PASS as instructors already have this capability
        """
        driver = instructor_auth
        wait = WebDriverWait(driver, 10)

        # Look for course generation in instructor dashboard
        # (This already exists in instructor-dashboard.html)
        generate_section = wait.until(
            EC.presence_of_element_located((By.ID, "generate-section"))
        )

        assert generate_section is not None, "Instructor should have course generation capability"
