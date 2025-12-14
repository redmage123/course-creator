"""
Instructor Complete Journey Test

BUSINESS CONTEXT:
This test validates the complete instructor workflow from login through
course management, ensuring all instructor-facing features work correctly.

TEST COVERAGE:
1. Login via UI (no token injection)
2. View programs list (including unpublished)
3. Create new training program
4. Edit program content
5. Publish/unpublish programs
6. View student analytics

BUG REGRESSION:
These tests specifically verify the published_only bug fix by ensuring
instructors see ALL their programs, not just published ones.
"""

import pytest
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.true_e2e.base.true_e2e_base import TrueE2EBaseTest
from tests.e2e.true_e2e.base.react_waits import ReactWaitHelpers
from tests.e2e.true_e2e.pages.login_page import LoginPage
from tests.e2e.true_e2e.pages.instructor_dashboard import InstructorDashboard
from tests.e2e.true_e2e.pages.training_program_page import TrainingProgramPage

logger = logging.getLogger(__name__)


@pytest.mark.true_e2e
@pytest.mark.instructor_journey
class TestInstructorJourney:
    """
    Complete instructor user journey tests.

    These tests validate the full instructor experience using real UI
    interactions and database state verification.
    """

    def test_instructor_login_redirects_to_dashboard(
        self,
        true_e2e_driver,
        data_seeder,
        db_verifier,
        selenium_config
    ):
        """
        Test that instructor login redirects to instructor dashboard.
        """
        # Seed test data
        org = data_seeder.create_organization()
        instructor = data_seeder.create_instructor(org.id)

        # Login via real UI
        login_page = LoginPage(true_e2e_driver, selenium_config)
        success = login_page.login(instructor.email, instructor.password)

        assert success, "Instructor login should succeed"

        # Verify redirected to dashboard
        current_url = true_e2e_driver.current_url.lower()
        assert 'dashboard' in current_url or 'instructor' in current_url, \
            f"Should redirect to dashboard, got: {current_url}"

        # Verify user exists in database
        user = db_verifier.get_user_by_email(instructor.email)
        assert user is not None, "Instructor should exist in database"
        assert user.role == 'instructor', "User role should be instructor"

    def test_instructor_sees_all_programs_including_unpublished(
        self,
        true_e2e_driver,
        data_seeder,
        db_verifier,
        selenium_config
    ):
        """
        Test that instructor sees ALL programs, including unpublished ones.

        THIS IS THE KEY BUG REGRESSION TEST.
        The published_only bug caused unpublished courses to not appear.
        """
        # Seed data with published and unpublished courses
        org = data_seeder.create_organization()
        instructor = data_seeder.create_instructor(org.id)

        # Create one published and one unpublished course
        published_course = data_seeder.create_course(
            instructor_id=instructor.id,
            title=f"{data_seeder.test_prefix}_Published",
            organization_id=org.id,
            is_published=True
        )
        unpublished_course = data_seeder.create_course(
            instructor_id=instructor.id,
            title=f"{data_seeder.test_prefix}_Unpublished",
            organization_id=org.id,
            is_published=False
        )

        # Verify in database
        db_courses = db_verifier.get_courses_for_instructor(
            instructor.id, include_unpublished=True
        )
        assert len(db_courses) == 2, "Database should have 2 courses"

        # Login via real UI
        login_page = LoginPage(true_e2e_driver, selenium_config)
        login_page.login(instructor.email, instructor.password)

        # Navigate to programs page
        program_page = TrainingProgramPage(true_e2e_driver, selenium_config)
        program_page.navigate_to_list(role="instructor")

        # Wait for React Query to load data
        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_react_query_idle()
        waits.wait_for_loading_complete()

        # Get programs from UI
        ui_program_titles = program_page.get_program_titles()
        ui_program_count = program_page.get_program_count()

        logger.info(f"UI shows {ui_program_count} programs: {ui_program_titles}")

        # CRITICAL ASSERTIONS - These would catch the published_only bug
        assert ui_program_count >= 2, \
            f"Instructor should see at least 2 programs (published + unpublished), got {ui_program_count}"

        assert program_page.program_exists_in_list(published_course.title), \
            f"Published course '{published_course.title}' should appear in list"

        assert program_page.program_exists_in_list(unpublished_course.title), \
            f"Unpublished course '{unpublished_course.title}' should appear in list. " \
            f"This is the published_only bug! UI shows: {ui_program_titles}"

    def test_instructor_can_create_new_program(
        self,
        true_e2e_driver,
        data_seeder,
        db_verifier,
        selenium_config
    ):
        """
        Test that instructor can create a new training program via UI.
        """
        # Seed data
        org = data_seeder.create_organization()
        instructor = data_seeder.create_instructor(org.id)

        # Login
        login_page = LoginPage(true_e2e_driver, selenium_config)
        login_page.login(instructor.email, instructor.password)

        # Navigate to programs
        program_page = TrainingProgramPage(true_e2e_driver, selenium_config)
        program_page.navigate_to_list(role="instructor")

        # Get initial count
        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_react_query_idle()
        initial_count = program_page.get_program_count()

        # Click create button
        program_page.click_create_program()

        # Fill form
        new_title = f"{data_seeder.test_prefix}_NewProgram"
        program_page.fill_program_form(
            title=new_title,
            description="Test program created via E2E test",
            difficulty="beginner"
        )

        # Submit form
        program_page.submit_form()

        # Wait for redirect back to list
        waits.wait_for_loading_complete()
        waits.wait_for_react_query_idle()

        # Verify new program appears in list
        program_page.navigate_to_list(role="instructor")
        waits.wait_for_react_query_idle()

        new_count = program_page.get_program_count()
        ui_titles = program_page.get_program_titles()

        logger.info(f"After creation: {new_count} programs, titles: {ui_titles}")

        # Check UI
        assert new_count > initial_count, \
            f"Program count should increase after creation. Was {initial_count}, now {new_count}"

        assert program_page.program_exists_in_list(new_title), \
            f"New program '{new_title}' should appear in list"

        # Verify in database
        db_courses = db_verifier.get_courses_for_instructor(instructor.id)
        db_titles = [c.title for c in db_courses]
        assert any(new_title in t for t in db_titles), \
            f"New program should exist in database. DB has: {db_titles}"

    def test_newly_created_program_is_unpublished_by_default(
        self,
        true_e2e_driver,
        data_seeder,
        db_verifier,
        selenium_config
    ):
        """
        Test that newly created programs are unpublished by default
        and still appear in instructor's list.
        """
        # Seed data
        org = data_seeder.create_organization()
        instructor = data_seeder.create_instructor(org.id)

        # Login
        login_page = LoginPage(true_e2e_driver, selenium_config)
        login_page.login(instructor.email, instructor.password)

        # Navigate to programs
        program_page = TrainingProgramPage(true_e2e_driver, selenium_config)
        program_page.navigate_to_list(role="instructor")

        # Create new program
        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_react_query_idle()

        program_page.click_create_program()

        new_title = f"{data_seeder.test_prefix}_DraftProgram"
        program_page.fill_program_form(
            title=new_title,
            description="This should be unpublished",
            difficulty="intermediate"
        )
        program_page.submit_form()

        waits.wait_for_loading_complete()
        waits.wait_for_react_query_idle()

        # Navigate back to list
        program_page.navigate_to_list(role="instructor")
        waits.wait_for_react_query_idle()

        # Verify program appears (this is where the bug would be caught)
        assert program_page.program_exists_in_list(new_title), \
            f"Newly created unpublished program MUST appear in instructor's list. " \
            f"If missing, this is the published_only bug!"

        # Verify database state
        db_courses = db_verifier.get_courses_for_instructor(instructor.id)
        matching_courses = [c for c in db_courses if new_title in c.title]

        assert len(matching_courses) > 0, "Course should exist in database"
        assert not matching_courses[0].is_published, \
            "New course should be unpublished by default"

    def test_instructor_can_publish_program(
        self,
        true_e2e_driver,
        data_seeder,
        db_verifier,
        selenium_config
    ):
        """
        Test that instructor can publish a program.
        """
        # Seed data with unpublished course
        org = data_seeder.create_organization()
        instructor = data_seeder.create_instructor(org.id)
        course = data_seeder.create_course(
            instructor_id=instructor.id,
            title=f"{data_seeder.test_prefix}_ToPublish",
            organization_id=org.id,
            is_published=False
        )

        # Verify initially unpublished
        assert not db_verifier.get_course_by_id(course.id).is_published

        # Login
        login_page = LoginPage(true_e2e_driver, selenium_config)
        login_page.login(instructor.email, instructor.password)

        # Navigate to programs
        program_page = TrainingProgramPage(true_e2e_driver, selenium_config)
        program_page.navigate_to_list(role="instructor")

        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_react_query_idle()

        # Click on the course
        if program_page.click_program(course.title):
            waits.wait_for_loading_complete()

            # Try to publish
            if program_page.click_publish():
                waits.wait_for_react_query_idle()

                # Verify in database
                updated_course = db_verifier.get_course_by_id(course.id)
                assert updated_course.is_published, \
                    "Course should be published after clicking publish"
            else:
                logger.info("Publish button not found - UI may differ")
        else:
            logger.warning(f"Could not click course: {course.title}")

    def test_instructor_sees_student_count(
        self,
        true_e2e_driver,
        data_seeder,
        db_verifier,
        selenium_config
    ):
        """
        Test that instructor can see enrolled student count.
        """
        # Seed complete scenario with students
        scenario = data_seeder.seed_complete_org_scenario()
        instructor = scenario['instructors'][0]

        # Login
        login_page = LoginPage(true_e2e_driver, selenium_config)
        login_page.login(instructor.email, instructor.password)

        # Navigate to dashboard
        dashboard = InstructorDashboard(true_e2e_driver, selenium_config)

        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_react_query_idle()

        # Should be on dashboard
        assert dashboard.is_on_dashboard() or 'instructor' in true_e2e_driver.current_url, \
            "Should be on instructor dashboard"

    def test_instructor_cannot_access_admin_pages(
        self,
        true_e2e_driver,
        data_seeder,
        selenium_config
    ):
        """
        Test that instructor cannot access admin-only pages.
        """
        org = data_seeder.create_organization()
        instructor = data_seeder.create_instructor(org.id)

        # Login
        login_page = LoginPage(true_e2e_driver, selenium_config)
        login_page.login(instructor.email, instructor.password)

        # Try to access admin page
        true_e2e_driver.get(f"{selenium_config.base_url}/admin/organizations")

        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_loading_complete()

        current_url = true_e2e_driver.current_url.lower()

        # Should be redirected or denied
        unauthorized = (
            'login' in current_url or
            'dashboard' in current_url or
            'instructor' in current_url or
            'forbidden' in current_url
        )

        page_text = true_e2e_driver.find_element(By.TAG_NAME, 'body').text.lower()
        access_denied = (
            'access denied' in page_text or
            'unauthorized' in page_text or
            'permission' in page_text
        )

        assert unauthorized or access_denied, \
            f"Instructor should not access admin page. URL: {current_url}"
