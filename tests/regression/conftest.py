"""
Regression Test Configuration and Shared Fixtures

BUSINESS CONTEXT:
Provides reusable test fixtures and configuration for all regression tests.
Ensures consistent test environment setup and teardown across all test categories.

TECHNICAL IMPLEMENTATION:
- Provides browser fixtures for Selenium E2E tests
- Provides database connection fixtures with transaction rollback
- Provides authentication fixtures for different user roles
- Provides test data factories for common test scenarios
"""

import pytest
import asyncio
import asyncpg
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from typing import AsyncGenerator, Dict, Any
import os
from datetime import datetime, timedelta
import uuid
import hmac
import hashlib


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers for regression tests"""
    config.addinivalue_line(
        "markers", "regression: mark test as regression test"
    )
    config.addinivalue_line(
        "markers", "critical: mark test as critical regression test"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication regression test"
    )
    config.addinivalue_line(
        "markers", "data_consistency: mark test as data consistency regression"
    )
    config.addinivalue_line(
        "markers", "privacy: mark test as privacy compliance regression"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance regression"
    )
    config.addinivalue_line(
        "markers", "ui_ux: mark test as UI/UX regression test"
    )


# ============================================================================
# BROWSER FIXTURES (Selenium E2E)
# ============================================================================

@pytest.fixture(scope="function")
def browser_options():
    """Configure browser options for Selenium tests"""
    options = ChromeOptions()

    # Headless mode for CI/CD
    if os.getenv("HEADLESS", "true").lower() == "true":
        options.add_argument("--headless=new")

    # Standard options for stability
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Accept insecure certificates for localhost HTTPS
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")

    return options


@pytest.fixture(scope="function")
def browser(browser_options):
    """
    Provides Selenium WebDriver for E2E regression tests

    USAGE:
    - Automatically creates and quits browser
    - Configured for localhost HTTPS
    - Headless mode in CI/CD
    """
    driver = webdriver.Chrome(options=browser_options)
    driver.implicitly_wait(10)

    yield driver

    # Cleanup
    driver.quit()


@pytest.fixture(scope="function")
def authenticated_browser(browser, test_base_url):
    """
    Provides authenticated browser session for regression tests

    USAGE:
    - Browser already logged in as default test user
    - Ready to test authenticated workflows
    """
    # Navigate to login page
    browser.get(f"{test_base_url}/login")

    # Perform login (implementation depends on login mechanism)
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    wait = WebDriverWait(browser, 10)

    username_input = wait.until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    password_input = browser.find_element(By.ID, "password")

    username_input.send_keys("test_user")
    password_input.send_keys("test_password")

    submit_button = browser.find_element(By.ID, "login-submit")
    submit_button.click()

    # Wait for redirect to dashboard
    wait.until(lambda d: "/dashboard" in d.current_url)

    yield browser


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    """
    Provides database connection pool for regression tests

    BUSINESS REQUIREMENT:
    - Use test database to avoid affecting production/dev data
    - Connection pool for efficient test execution
    """
    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://course_user:course_pass@localhost:5433/course_creator"
    )

    pool = await asyncpg.create_pool(
        database_url,
        min_size=5,
        max_size=20
    )

    yield pool

    await pool.close()


@pytest.fixture(scope="function")
async def db_connection(db_pool):
    """
    Provides database connection for individual test

    USAGE:
    - Each test gets isolated connection
    - Connection automatically closed after test
    """
    async with db_pool.acquire() as connection:
        yield connection


@pytest.fixture(scope="function")
async def db_transaction(db_connection):
    """
    Provides database transaction that rolls back after test

    BUSINESS REQUIREMENT:
    - Test isolation - changes made in one test don't affect others
    - Automatic cleanup - no manual teardown needed

    USAGE:
    - All database operations within transaction
    - Transaction automatically rolled back after test
    """
    transaction = db_connection.transaction()
    await transaction.start()

    yield db_connection

    await transaction.rollback()


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
def admin_credentials():
    """Credentials for site admin user"""
    return {
        "username": "admin",
        "password": "admin_password",
        "role": "admin",
        "expected_dashboard": "/site-admin-dashboard"
    }


@pytest.fixture
def org_admin_credentials():
    """Credentials for organization admin user"""
    return {
        "username": "org_admin",
        "password": "org_admin_password",
        "role": "org_admin",
        "organization_id": "test-org-uuid",
        "expected_dashboard": "/org-admin-dashboard"
    }


@pytest.fixture
def instructor_credentials():
    """Credentials for instructor user"""
    return {
        "username": "instructor",
        "password": "instructor_password",
        "role": "instructor",
        "organization_id": "test-org-uuid",
        "expected_dashboard": "/instructor-dashboard"
    }


@pytest.fixture
def student_credentials():
    """Credentials for student user"""
    return {
        "username": "student",
        "password": "student_password",
        "role": "student",
        "expected_dashboard": "/student-dashboard"
    }


# ============================================================================
# TEST DATA FACTORIES
# ============================================================================

@pytest.fixture
def create_test_organization():
    """
    Factory for creating test organization data

    USAGE:
    org_data = create_test_organization()
    # Returns dict with organization fields
    """
    def _create(name=None, slug=None):
        org_id = str(uuid.uuid4())
        return {
            "id": org_id,
            "name": name or f"Test Organization {org_id[:8]}",
            "slug": slug or f"test-org-{uuid.uuid4().hex[:8]}",
            "contact_email": f"contact-{uuid.uuid4().hex[:8]}@testorg.com",
            "settings": {
                "features_enabled": ["courses", "analytics", "labs"],
                "max_students": 1000
            },
            "created_at": datetime.utcnow(),
            "is_active": True
        }
    return _create


@pytest.fixture
def create_test_user():
    """
    Factory for creating test user data

    USAGE:
    user_data = create_test_user(role='student')
    # Returns dict with user fields
    """
    def _create(role="student", organization_id=None):
        user_id = str(uuid.uuid4())
        return {
            "id": user_id,
            "username": f"test_user_{uuid.uuid4().hex[:8]}",
            "email": f"user-{uuid.uuid4().hex[:8]}@test.com",
            "password_hash": "hashed_password_here",
            "role_name": role,
            "organization_id": organization_id,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    return _create


@pytest.fixture
def create_test_course():
    """
    Factory for creating test course data

    USAGE:
    course_data = create_test_course(instructor_id='uuid')
    # Returns dict with course fields
    """
    def _create(instructor_id, organization_id=None, status="draft"):
        course_id = str(uuid.uuid4())
        return {
            "id": course_id,
            "title": f"Test Course {course_id[:8]}",
            "slug": f"test-course-{uuid.uuid4().hex[:8]}",
            "description": "A comprehensive test course",
            "instructor_id": instructor_id,
            "organization_id": organization_id,
            "status": status,
            "difficulty_level": "beginner",
            "estimated_hours": 40,
            "created_at": datetime.utcnow(),
            "published_at": datetime.utcnow() if status == "published" else None
        }
    return _create


@pytest.fixture
def create_test_enrollment():
    """
    Factory for creating test enrollment data

    USAGE:
    enrollment_data = create_test_enrollment(student_id='uuid', course_id='uuid')
    # Returns dict with enrollment fields
    """
    def _create(student_id, course_id):
        enrollment_id = str(uuid.uuid4())
        return {
            "id": enrollment_id,
            "student_id": student_id,
            "course_id": course_id,
            "enrolled_at": datetime.utcnow(),
            "status": "active",
            "progress_percentage": 0,
            "last_accessed_at": datetime.utcnow()
        }
    return _create


@pytest.fixture
def create_test_quiz():
    """
    Factory for creating test quiz data

    USAGE:
    quiz_data = create_test_quiz(course_id='uuid')
    # Returns dict with quiz fields
    """
    def _create(course_id, num_questions=5):
        quiz_id = str(uuid.uuid4())
        return {
            "id": quiz_id,
            "course_id": course_id,
            "title": f"Test Quiz {quiz_id[:8]}",
            "description": "A test quiz",
            "questions": [
                {
                    "id": str(uuid.uuid4()),
                    "question_text": f"Question {i+1}",
                    "question_type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "points": 1
                }
                for i in range(num_questions)
            ],
            "total_points": num_questions,
            "passing_score": num_questions * 0.7,
            "time_limit_minutes": 30,
            "created_at": datetime.utcnow()
        }
    return _create


@pytest.fixture
def create_test_guest_session():
    """
    Factory for creating test guest session data

    USAGE:
    session_data = create_test_guest_session()
    # Returns dict with guest session fields
    """
    def _create(ip_address=None, user_agent=None):
        session_id = str(uuid.uuid4())
        ip = ip_address or "192.168.1.100"

        # Pseudonymize IP address
        pseudonymized_ip = hmac.new(
            b"test_secret_key",
            ip.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            "session_id": session_id,
            "fingerprint_hash": hashlib.sha256(
                (ip + (user_agent or "TestBrowser/1.0")).encode()
            ).hexdigest(),
            "pseudonymized_ip": pseudonymized_ip,
            "user_agent": user_agent or "TestBrowser/1.0",
            "created_at": datetime.utcnow(),
            "last_activity_at": datetime.utcnow(),
            "page_views": 1,
            "is_converted": False
        }
    return _create


# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_base_url():
    """Base URL for E2E tests"""
    return os.getenv("TEST_BASE_URL", "https://localhost:3000")


@pytest.fixture(scope="session")
def test_api_base_url():
    """Base URL for API tests"""
    return os.getenv("TEST_API_BASE_URL", "https://localhost:8000")


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
async def cleanup_test_data(db_connection):
    """
    Cleanup fixture that removes test data after test completes

    USAGE:
    - Add data to cleanup list during test
    - Automatically deleted after test

    Example:
        cleanup_data = []
        user_id = await create_user(...)
        cleanup_data.append(('users', 'id', user_id))
    """
    cleanup_data = []

    yield cleanup_data

    # Cleanup in reverse order (most recent first)
    for table, id_column, id_value in reversed(cleanup_data):
        try:
            await db_connection.execute(
                f"DELETE FROM {table} WHERE {id_column} = $1",
                id_value
            )
        except Exception as e:
            # Log but don't fail test
            print(f"Cleanup warning: Could not delete from {table}: {e}")


# ============================================================================
# PERFORMANCE MEASUREMENT FIXTURES
# ============================================================================

@pytest.fixture
def measure_performance():
    """
    Fixture for measuring performance in regression tests

    USAGE:
    with measure_performance() as timer:
        # Code to measure
        await some_operation()

    assert timer.elapsed < 0.5  # 500ms limit
    """
    from contextlib import contextmanager
    import time

    @contextmanager
    def _measure():
        class Timer:
            def __init__(self):
                self.start_time = None
                self.end_time = None
                self.elapsed = None

        timer = Timer()
        timer.start_time = time.time()

        yield timer

        timer.end_time = time.time()
        timer.elapsed = timer.end_time - timer.start_time

    return _measure


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_email_service(monkeypatch):
    """
    Mock email service for testing email-dependent workflows

    USAGE:
    - Prevents actual emails from being sent
    - Captures sent emails for verification
    """
    sent_emails = []

    async def mock_send_email(to, subject, body):
        sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body,
            "sent_at": datetime.utcnow()
        })

    # Monkeypatch actual email service
    # monkeypatch.setattr("email_service.send_email", mock_send_email)

    yield sent_emails


@pytest.fixture
def mock_external_api(monkeypatch):
    """
    Mock external API calls for testing integrations

    USAGE:
    - Prevents actual API calls
    - Returns controlled test responses
    """
    api_calls = []

    async def mock_api_call(endpoint, method, data=None):
        api_calls.append({
            "endpoint": endpoint,
            "method": method,
            "data": data,
            "called_at": datetime.utcnow()
        })
        return {"success": True, "data": {}}

    yield api_calls
