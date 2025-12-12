"""
Base Test Classes

BUSINESS CONTEXT:
All tests should inherit from these base classes to ensure consistent
testing patterns, proper setup/teardown, and validation.

TECHNICAL IMPLEMENTATION:
- BaseUnitTest: For isolated unit tests
- BaseIntegrationTest: For integration tests with services
- BaseE2ETest: For end-to-end browser tests

TEST COVERAGE:
- Proper test isolation
- Consistent error handling
- Shared test utilities
"""

import pytest
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import requests


class BaseTest:
    """
    Base class for all tests

    Provides:
    - Project root path
    - Common test utilities
    - Error handling
    """

    @classmethod
    def setup_class(cls):
        """Setup run once before all tests in class"""
        # Add project root to Python path
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

    @classmethod
    def teardown_class(cls):
        """Cleanup run once after all tests in class"""
        pass

    def setup_method(self):
        """Setup run before each test method"""
        pass

    def teardown_method(self):
        """Cleanup run after each test method"""
        pass


class BaseUnitTest(BaseTest):
    """
    Base class for unit tests

    CRITICAL REQUIREMENTS:
    - Must test in isolation (no external dependencies)
    - Must use mocks for external services
    - Must be fast (<100ms per test)
    - Must validate imports first

    USAGE:
        class TestMyService(BaseUnitTest):
            def test_something(self):
                # Your test here
                pass
    """

    @classmethod
    def setup_class(cls):
        """Setup for unit tests"""
        super().setup_class()
        # Unit tests should validate imports
        cls._validate_imports()

    @classmethod
    def _validate_imports(cls):
        """
        Validate that the module under test can be imported

        Override this in subclasses to test specific imports
        """
        pass

    def create_mock_response(
        self,
        status_code: int = 200,
        json_data: Optional[Dict[str, Any]] = None,
        text: str = ""
    ):
        """
        Create a mock HTTP response

        Args:
            status_code: HTTP status code
            json_data: JSON data to return
            text: Response text

        Returns:
            Mock response object
        """
        pytest.skip("Needs refactoring to use real objects")
        return None

    def create_mock_user(
        self,
        user_id: str = "test-user-123",
        email: str = "test@example.com",
        role: str = "student"
    ) -> Dict[str, Any]:
        """
        Create a mock user object

        Args:
            user_id: User ID
            email: User email
            role: User role

        Returns:
            Dictionary representing a user
        """
        return {
            'id': user_id,
            'email': email,
            'username': email.split('@')[0],
            'role': role,
            'role_type': role,
            'is_active': True
        }


class BaseIntegrationTest(BaseTest):
    """
    Base class for integration tests

    CRITICAL REQUIREMENTS:
    - Must verify services are running
    - Must setup test data
    - Must cleanup after tests
    - Must handle service failures gracefully

    USAGE:
        class TestMyIntegration(BaseIntegrationTest):
            service_url = "https://localhost:8000"

            def test_integration(self):
                # Your test here
                pass
    """

    service_url: Optional[str] = None
    requires_docker: bool = True

    @classmethod
    def setup_class(cls):
        """Setup for integration tests"""
        super().setup_class()

        # Verify services are running
        if cls.requires_docker:
            cls._verify_services_running()

    @classmethod
    def _verify_services_running(cls):
        """
        Verify required services are running

        Raises:
            pytest.skip: If services are not running
        """
        import docker

        try:
            client = docker.from_env()
            containers = client.containers.list()

            if not containers:
                pytest.skip("No Docker containers running. Start services with: docker-compose up -d")

        except Exception as e:
            pytest.skip(f"Docker not available: {e}")

    def make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        expected_status: Optional[int] = None,
        timeout: int = 10
    ) -> requests.Response:
        """
        Make an HTTP request to a service

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            headers: Request headers
            json: JSON data
            expected_status: Expected HTTP status code
            timeout: Request timeout in seconds

        Returns:
            Response object

        Raises:
            AssertionError: If expected_status doesn't match
        """
        if not self.service_url:
            pytest.fail("service_url must be set in test class")

        url = f"{self.service_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json,
                verify=False,
                timeout=timeout
            )

            if expected_status is not None:
                assert response.status_code == expected_status, \
                    f"Expected {expected_status}, got {response.status_code}: {response.text}"

            return response

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Request failed: {e}")

    def get_auth_token(self, role: str = "site_admin") -> str:
        """
        Get authentication token for testing

        Args:
            role: User role

        Returns:
            Authentication token

        Note:
            Override this in subclasses to use real authentication
        """
        return f"mock-token-{role}"


class BaseE2ETest(BaseTest):
    """
    Base class for E2E tests

    CRITICAL REQUIREMENTS:
    - Must use real browser
    - Must test actual user workflows
    - Must verify visual elements
    - Must cleanup browser sessions

    USAGE:
        class TestMyE2E(BaseE2ETest):
            def test_user_workflow(self):
                # Your test here
                pass
    """

    driver = None
    base_url: str = "https://localhost:3000"

    @classmethod
    def setup_class(cls):
        """Setup for E2E tests"""
        super().setup_class()
        # Import will fail if selenium not available
        try:
            from selenium import webdriver
        except ImportError:
            pytest.skip("Selenium not installed")

    def setup_method(self):
        """Setup browser for each test"""
        super().setup_method()
        # Subclasses should initialize driver if needed

    def teardown_method(self):
        """Cleanup browser after each test"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        super().teardown_method()

    def wait_for_element(self, locator, timeout=10):
        """
        Wait for element to be present

        Args:
            locator: Tuple of (By.X, "selector")
            timeout: Timeout in seconds

        Returns:
            WebElement

        Raises:
            TimeoutException: If element not found
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def click_element_js(self, element):
        """
        Click element using JavaScript (avoids some Selenium issues)

        Args:
            element: WebElement to click
        """
        self.driver.execute_script("arguments[0].click();", element)
