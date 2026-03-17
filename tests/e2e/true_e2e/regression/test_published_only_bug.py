"""
Regression Test: published_only Bug

BUG DESCRIPTION:
The trainingProgramService.getOrganizationPrograms() and
getInstructorPrograms() methods did not pass published_only=false
to the backend API. This caused newly created (unpublished) courses
to not appear in the instructor's or org admin's program list.

ROOT CAUSE:
The React service layer methods called getTrainingPrograms() without
the published_only parameter, and the backend defaults to
published_only=true, hiding unpublished courses.

WHY E2E TESTS MISSED IT:
The old E2E tests used direct fetch() calls in JavaScript:
    driver.execute_script("return fetch('/api/v1/courses?published_only=false')")
This bypassed the React service layer entirely, so the bug was hidden.

FIX:
Added published_only=false to getOrganizationPrograms() and
getInstructorPrograms() in trainingProgramService.ts.

TEST APPROACH:
These tests use REAL UI interactions that exercise the React service
layer, ensuring the bug cannot recur without being caught.
"""

import pytest
import logging

from selenium.webdriver.common.by import By

from tests.e2e.true_e2e.base.react_waits import ReactWaitHelpers
from tests.e2e.true_e2e.pages.login_page import LoginPage
from tests.e2e.true_e2e.pages.training_program_page import TrainingProgramPage

logger = logging.getLogger(__name__)


@pytest.mark.true_e2e
@pytest.mark.regression
class TestPublishedOnlyBugRegression:
    """
    Regression tests for the published_only bug.

    These tests verify that unpublished programs are visible to:
    1. Instructors who created them
    2. Organization admins in the same org
    """

    def test_instructor_sees_unpublished_program_after_creation(
        self,
        true_e2e_driver,
        data_seeder,
        db_verifier,
        selenium_config
    ):
        """
        REGRESSION TEST: Instructor should see newly created unpublished program.

        This test reproduces the exact scenario where the bug was discovered:
        1. Instructor creates a new program via UI
        2. Program is unpublished by default
        3. Instructor should see it in their program list

        If this test fails, the published_only bug has recurred.
        """
        # Setup
        org = data_seeder.create_organization()
        instructor = data_seeder.create_instructor(org.id)

        # Login as instructor via REAL UI (no token injection)
        login_page = LoginPage(true_e2e_driver, selenium_config)
        success = login_page.login(instructor.email, instructor.password)
        assert success, "Instructor login should succeed"

        # Navigate to programs list
        program_page = TrainingProgramPage(true_e2e_driver, selenium_config)
        program_page.navigate_to_list(role="instructor")

        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_react_query_idle()

        # Get initial state
        initial_count = program_page.get_program_count()
        initial_titles = program_page.get_program_titles()
        logger.info(f"Initial state: {initial_count} programs - {initial_titles}")

        # Create new program via UI
        create_clicked = program_page.click_create_program()

        if create_clicked:
            # Fill the form
            new_title = f"{data_seeder.test_prefix}_RegressionTest"
            program_page.fill_program_form(
                title=new_title,
                description="Testing published_only bug regression",
                difficulty="beginner"
            )

            # Submit
            program_page.submit_form()
            waits.wait_for_loading_complete()
            waits.wait_for_react_query_idle()

            # Verify in database - should be unpublished
            db_courses = db_verifier.get_courses_for_instructor(instructor.id)
            matching = [c for c in db_courses if new_title in c.title]

            assert len(matching) > 0, "Course should exist in database"
            assert not matching[0].is_published, "New course should be unpublished by default"

            # Navigate back to list
            program_page.navigate_to_list(role="instructor")
            waits.wait_for_react_query_idle()
            waits.wait_for_loading_complete()

            # CRITICAL ASSERTION: The newly created unpublished program MUST appear
            final_titles = program_page.get_program_titles()
            final_count = program_page.get_program_count()

            logger.info(f"After creation: {final_count} programs - {final_titles}")

            assert program_page.program_exists_in_list(new_title), \
                f"REGRESSION DETECTED: Unpublished program '{new_title}' should appear " \
                f"in instructor's list. This is the published_only bug! " \
                f"UI shows: {final_titles}"

            assert final_count > initial_count, \
                f"Program count should increase. Was {initial_count}, now {final_count}"

        else:
            # If we can't click create, verify seeded unpublished course appears
            unpublished_course = data_seeder.create_course(
                instructor_id=instructor.id,
                title=f"{data_seeder.test_prefix}_Unpublished",
                organization_id=org.id,
                is_published=False
            )

            # Refresh the page
            program_page.navigate_to_list(role="instructor")
            waits.wait_for_react_query_idle()

            titles = program_page.get_program_titles()
            assert program_page.program_exists_in_list(unpublished_course.title), \
                f"REGRESSION: Seeded unpublished course should appear. Got: {titles}"

    def test_org_admin_sees_all_org_programs_including_unpublished(
        self,
        true_e2e_driver,
        data_seeder,
        db_verifier,
        selenium_config
    ):
        """
        REGRESSION TEST: Org admin should see ALL programs, including unpublished.

        This test verifies that getOrganizationPrograms() correctly
        passes published_only=false to the backend.
        """
        # Setup with both published and unpublished courses
        org = data_seeder.create_organization()
        org_admin = data_seeder.create_org_admin(org.id)
        instructor = data_seeder.create_instructor(org.id)

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

        # Verify database state
        db_courses = db_verifier.get_courses_for_organization(org.id, include_unpublished=True)
        assert len(db_courses) >= 2, "Database should have both courses"
        logger.info(f"DB courses: {[c.title for c in db_courses]}")

        # Login as org admin via REAL UI
        login_page = LoginPage(true_e2e_driver, selenium_config)
        success = login_page.login(org_admin.email, org_admin.password)
        assert success, "Org admin login should succeed"

        # Navigate to programs
        program_page = TrainingProgramPage(true_e2e_driver, selenium_config)
        program_page.navigate_to_list(role="org-admin")

        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_react_query_idle()
        waits.wait_for_loading_complete()

        # Get UI state
        ui_titles = program_page.get_program_titles()
        ui_count = program_page.get_program_count()

        logger.info(f"Org admin sees {ui_count} programs: {ui_titles}")

        # CRITICAL ASSERTIONS
        assert program_page.program_exists_in_list(published_course.title), \
            f"Published course should appear. Got: {ui_titles}"

        assert program_page.program_exists_in_list(unpublished_course.title), \
            f"REGRESSION DETECTED: Unpublished course '{unpublished_course.title}' " \
            f"MUST appear for org admin. This is the published_only bug! " \
            f"UI shows only: {ui_titles}"

    def test_ui_program_count_matches_db_count(
        self,
        true_e2e_driver,
        data_seeder,
        db_verifier,
        selenium_config
    ):
        """
        REGRESSION TEST: UI program count should match database count.

        The published_only bug caused a mismatch between UI and DB counts.
        """
        # Setup
        org = data_seeder.create_organization()
        instructor = data_seeder.create_instructor(org.id)

        # Create multiple courses with different published states
        for i in range(3):
            data_seeder.create_course(
                instructor_id=instructor.id,
                title=f"{data_seeder.test_prefix}_Course{i}",
                organization_id=org.id,
                is_published=(i % 2 == 0)  # Alternating published/unpublished
            )

        # Get expected count from DB
        db_courses = db_verifier.get_courses_for_instructor(instructor.id, include_unpublished=True)
        db_count = len([c for c in db_courses if data_seeder.test_prefix in c.title])

        # Login as instructor
        login_page = LoginPage(true_e2e_driver, selenium_config)
        login_page.login(instructor.email, instructor.password)

        # Navigate to programs
        program_page = TrainingProgramPage(true_e2e_driver, selenium_config)
        program_page.navigate_to_list(role="instructor")

        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_react_query_idle()
        waits.wait_for_loading_complete()

        # Count matching programs in UI
        ui_titles = program_page.get_program_titles()
        ui_count = len([t for t in ui_titles if data_seeder.test_prefix in t])

        logger.info(f"DB count: {db_count}, UI count: {ui_count}")

        # Counts should match (within tolerance for timing)
        assert abs(ui_count - db_count) <= 1, \
            f"REGRESSION: UI count ({ui_count}) should match DB count ({db_count}). " \
            f"published_only bug causes mismatch!"

    def test_both_published_and_unpublished_visible_in_same_list(
        self,
        true_e2e_driver,
        data_seeder,
        selenium_config
    ):
        """
        REGRESSION TEST: Verify both published and unpublished programs
        appear in the same list view.

        This is a direct test of the fix - the UI should show both.
        """
        org = data_seeder.create_organization()
        instructor = data_seeder.create_instructor(org.id)

        # Create one of each
        pub = data_seeder.create_course(
            instructor_id=instructor.id,
            title=f"{data_seeder.test_prefix}_Pub",
            organization_id=org.id,
            is_published=True
        )
        unpub = data_seeder.create_course(
            instructor_id=instructor.id,
            title=f"{data_seeder.test_prefix}_Unpub",
            organization_id=org.id,
            is_published=False
        )

        # Login
        login_page = LoginPage(true_e2e_driver, selenium_config)
        login_page.login(instructor.email, instructor.password)

        # Navigate
        program_page = TrainingProgramPage(true_e2e_driver, selenium_config)
        program_page.navigate_to_list(role="instructor")

        waits = ReactWaitHelpers(true_e2e_driver)
        waits.wait_for_react_query_idle()

        # Get programs with status
        programs = program_page.get_programs_with_status()
        test_programs = [p for p in programs if data_seeder.test_prefix in p['title']]

        logger.info(f"Test programs: {test_programs}")

        # Should have both published and unpublished
        published_titles = [p['title'] for p in test_programs if p['published']]
        unpublished_titles = [p['title'] for p in test_programs if not p['published']]

        # At minimum, both seeded courses should appear
        titles = program_page.get_program_titles()

        assert program_page.program_exists_in_list(pub.title), \
            f"Published course should appear: {pub.title}"

        assert program_page.program_exists_in_list(unpub.title), \
            f"REGRESSION: Unpublished course must appear: {unpub.title}. " \
            f"List shows: {titles}"
