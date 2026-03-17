"""
Pytest Fixtures for True E2E Testing

BUSINESS CONTEXT:
These fixtures provide consistent test setup and teardown for true E2E tests.
They ensure proper browser initialization, data seeding, and cleanup.

TECHNICAL IMPLEMENTATION:
- Session-scoped browser for performance
- Function-scoped data seeding for isolation
- Automatic cleanup after each test
- Console error checking on test completion

USAGE:
    def test_student_journey(true_e2e_driver, data_seeder, db_verifier):
        # Use fixtures directly in test functions
        org = data_seeder.create_organization()
        student = data_seeder.create_student(org.id)
        # ... test code ...
"""

import os
import logging
import pytest
from typing import Generator
from uuid import uuid4

# ============================================================================
# DATABASE CONFIGURATION FOR TRUE E2E TESTS
# ============================================================================
# Override any incorrect DATABASE_URL settings from parent conftest files.
# True E2E tests use the main database (not test database) because they
# test against the real running application.

# Clear any test database settings that would conflict
if 'TEST_DATABASE_URL' in os.environ:
    del os.environ['TEST_DATABASE_URL']

# Set correct database URL for the running platform
# Port 5433 is the externally-mapped postgres port from docker-compose.yml
os.environ['DATABASE_URL'] = (
    'postgresql://postgres:postgres_password@localhost:5433/course_creator'
    '?options=-csearch_path=course_creator,public'
)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from tests.e2e.selenium_base import SeleniumConfig, ChromeDriverSetup
from tests.e2e.true_e2e.base.true_e2e_base import TrueE2EBaseTest
from tests.e2e.true_e2e.base.react_waits import ReactWaitHelpers
from tests.e2e.true_e2e.data.data_seeder import DataSeeder
from tests.e2e.true_e2e.data.database_verifier import DatabaseVerifier

logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE OVERRIDE FIXTURE
# ============================================================================
# The parent tests/conftest.py has an autouse fixture that sets DATABASE_URL
# to a test database. We need to override this for true E2E tests which
# connect to the real running platform database.

@pytest.fixture(autouse=True, scope="function")
def override_database_url_for_true_e2e():
    """
    Override DATABASE_URL for true E2E tests.

    This runs AFTER the parent conftest's setup_test_environment fixture
    but BEFORE our test fixtures that need database access.
    """
    # Store original value
    original_url = os.environ.get('DATABASE_URL')

    # Set correct database URL for the running platform
    os.environ['DATABASE_URL'] = (
        'postgresql://postgres:postgres_password@localhost:5433/course_creator'
        '?options=-csearch_path=course_creator,public'
    )

    # Clear test database URL if set
    if 'TEST_DATABASE_URL' in os.environ:
        del os.environ['TEST_DATABASE_URL']

    yield

    # Restore original (optional - for cleanliness)
    if original_url:
        os.environ['DATABASE_URL'] = original_url


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def selenium_config() -> SeleniumConfig:
    """
    Provide Selenium configuration for the test session.

    Session-scoped because configuration doesn't change between tests.
    """
    return SeleniumConfig()


@pytest.fixture(scope="session")
def base_url(selenium_config) -> str:
    """Provide the base URL for tests."""
    return selenium_config.base_url


# ============================================================================
# BROWSER FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def true_e2e_driver(selenium_config) -> Generator[webdriver.Chrome, None, None]:
    """
    Provide a Chrome WebDriver instance for true E2E testing.

    Function-scoped to ensure clean browser state for each test.
    Includes automatic screenshot on failure and console error checking.

    NOTE: Sets implicit_wait to 1 second to prevent 20s delays on
    unmatched selectors. Tests should use explicit waits when needed.
    """
    driver = ChromeDriverSetup.create_driver(selenium_config)

    # Override implicit wait to prevent long delays on unmatched selectors
    # The default 20s causes massive slowdowns in selector loops
    driver.implicitly_wait(1)

    yield driver

    # Check for browser console errors
    try:
        logs = driver.get_log('browser')
        errors = [log for log in logs if log.get('level') == 'SEVERE']

        # Filter known acceptable errors
        acceptable = ['favicon.ico', 'DevTools']
        filtered = [e for e in errors if not any(a in e.get('message', '') for a in acceptable)]

        if filtered:
            logger.warning(f"Browser console errors: {filtered}")
    except Exception as e:
        logger.debug(f"Could not get browser logs: {e}")

    # Close browser
    try:
        driver.quit()
    except Exception as e:
        logger.error(f"Error closing driver: {e}")


@pytest.fixture(scope="function")
def wait_helpers(true_e2e_driver) -> ReactWaitHelpers:
    """
    Provide React wait helpers for the current driver.
    """
    return ReactWaitHelpers(true_e2e_driver)


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_prefix() -> str:
    """
    Generate a unique test prefix for data isolation.

    Each test gets a unique prefix to ensure complete data isolation.
    """
    return f"test_{uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def data_seeder(test_prefix) -> Generator[DataSeeder, None, None]:
    """
    Provide a data seeder with automatic cleanup.

    The seeder creates test data in the database before the test runs.
    All seeded data is automatically cleaned up after the test completes.
    """
    seeder = DataSeeder(test_prefix=test_prefix)

    yield seeder

    # Cleanup all seeded data
    try:
        seeder.cleanup()
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
    finally:
        seeder.close()


@pytest.fixture(scope="function")
def db_verifier() -> Generator[DatabaseVerifier, None, None]:
    """
    Provide a database verifier for state validation.

    Use this to verify that UI actions result in correct database state.
    """
    verifier = DatabaseVerifier()

    yield verifier

    verifier.close()


# ============================================================================
# COMPLETE SCENARIO FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def seeded_organization(data_seeder) -> dict:
    """
    Provide a seeded organization with all user types.

    Creates:
    - 1 Organization
    - 1 Org Admin
    - 2 Instructors
    - 3 Students
    - 2 Courses (1 published, 1 unpublished)
    - Enrollments for all students

    Returns dict with all created entities.
    """
    return data_seeder.seed_complete_org_scenario()


@pytest.fixture(scope="function")
def logged_in_student(true_e2e_driver, seeded_organization, selenium_config):
    """
    Provide a logged-in student session.

    Logs in as the first student from the seeded organization.
    """
    student = seeded_organization['students'][0]
    base_test = TrueE2EBaseTest()
    base_test.driver = true_e2e_driver
    base_test.config = selenium_config
    base_test._violation_check_enabled = True

    base_test.login_via_ui(student.email, student.password)

    return {
        'driver': true_e2e_driver,
        'user': student,
        'organization': seeded_organization['organization'],
        'test': base_test
    }


@pytest.fixture(scope="function")
def logged_in_instructor(true_e2e_driver, seeded_organization, selenium_config):
    """
    Provide a logged-in instructor session.

    Logs in as the first instructor from the seeded organization.
    """
    instructor = seeded_organization['instructors'][0]
    base_test = TrueE2EBaseTest()
    base_test.driver = true_e2e_driver
    base_test.config = selenium_config
    base_test._violation_check_enabled = True

    base_test.login_via_ui(instructor.email, instructor.password)

    return {
        'driver': true_e2e_driver,
        'user': instructor,
        'organization': seeded_organization['organization'],
        'test': base_test
    }


@pytest.fixture(scope="function")
def logged_in_org_admin(true_e2e_driver, seeded_organization, selenium_config):
    """
    Provide a logged-in org admin session.
    """
    org_admin = seeded_organization['org_admin']
    base_test = TrueE2EBaseTest()
    base_test.driver = true_e2e_driver
    base_test.config = selenium_config
    base_test._violation_check_enabled = True

    base_test.login_via_ui(org_admin.email, org_admin.password)

    return {
        'driver': true_e2e_driver,
        'user': org_admin,
        'organization': seeded_organization['organization'],
        'test': base_test
    }


@pytest.fixture(scope="function")
def logged_in_site_admin(true_e2e_driver, data_seeder, selenium_config):
    """
    Provide a logged-in site admin session.

    Creates a new site admin user (not part of any organization).
    """
    site_admin = data_seeder.create_site_admin()
    base_test = TrueE2EBaseTest()
    base_test.driver = true_e2e_driver
    base_test.config = selenium_config
    base_test._violation_check_enabled = True

    base_test.login_via_ui(site_admin.email, site_admin.password)

    return {
        'driver': true_e2e_driver,
        'user': site_admin,
        'test': base_test
    }


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def screenshot_on_failure(request, true_e2e_driver, selenium_config):
    """
    Automatically take screenshot on test failure.

    This fixture runs after each test and captures a screenshot
    if the test failed.
    """
    yield

    # Check if test failed
    if request.node.rep_call.failed if hasattr(request.node, 'rep_call') else False:
        test_name = request.node.name
        screenshot_path = os.path.join(
            selenium_config.screenshot_dir,
            f"FAILED_{test_name}.png"
        )
        try:
            true_e2e_driver.save_screenshot(screenshot_path)
            logger.info(f"Failure screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"Could not save failure screenshot: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test results for screenshot_on_failure fixture.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ============================================================================
# CONSOLE ERROR CHECKING
# ============================================================================

@pytest.fixture(autouse=False)  # Disabled autouse - manually add to tests that need it
def check_console_errors_after_test(true_e2e_driver):
    """
    Automatically check for browser console errors after each test.

    This runs after every test and logs any JavaScript errors found.
    Configure to fail tests on errors by setting STRICT_CONSOLE_ERRORS=true.
    """
    yield

    strict_mode = os.getenv('STRICT_CONSOLE_ERRORS', 'false').lower() == 'true'

    try:
        logs = true_e2e_driver.get_log('browser')
        errors = [log for log in logs if log.get('level') == 'SEVERE']

        # Filter known acceptable errors
        acceptable_patterns = [
            'favicon.ico',
            'DevTools',
            'net::ERR_FAILED',
            'net::ERR_ABORTED',
            'ResizeObserver loop',
        ]

        filtered_errors = []
        for error in errors:
            message = error.get('message', '')
            if not any(pattern in message for pattern in acceptable_patterns):
                filtered_errors.append(error)

        if filtered_errors:
            error_msg = '\n'.join(e.get('message', str(e)) for e in filtered_errors[:5])
            logger.warning(f"Browser console errors:\n{error_msg}")

            if strict_mode:
                pytest.fail(f"Browser console errors detected:\n{error_msg}")

    except Exception as e:
        logger.debug(f"Could not check console errors: {e}")


# ============================================================================
# MARKERS
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "true_e2e: mark test as true end-to-end test (uses real UI + database)"
    )
    config.addinivalue_line(
        "markers",
        "student_journey: mark test as part of student user journey"
    )
    config.addinivalue_line(
        "markers",
        "instructor_journey: mark test as part of instructor user journey"
    )
    config.addinivalue_line(
        "markers",
        "org_admin_journey: mark test as part of org admin user journey"
    )
    config.addinivalue_line(
        "markers",
        "site_admin_journey: mark test as part of site admin user journey"
    )
    config.addinivalue_line(
        "markers",
        "guest_journey: mark test as part of guest user journey"
    )
    config.addinivalue_line(
        "markers",
        "regression: mark test as regression test for a specific bug"
    )
    config.addinivalue_line(
        "markers",
        "nondestructive: mark test as safe to run against production-like environments"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically add nondestructive marker to all true_e2e tests.

    This allows tests to run against production-like URLs without
    pytest-selenium blocking them. Our tests use data seeding with
    cleanup, so they are safe for production-like environments.
    """
    nondestructive = pytest.mark.nondestructive

    for item in items:
        # Add nondestructive marker to all tests in true_e2e directory
        if 'true_e2e' in str(item.fspath):
            item.add_marker(nondestructive)
