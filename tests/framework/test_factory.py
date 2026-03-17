"""
Test Factory Module
Single Responsibility: Create test-related objects
Open/Closed: Extensible factory system
Dependency Inversion: Uses abstractions for creation
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from .test_config import TestConfig, TestSuiteConfig, TestType, TestPriority
from .test_suite import ITestSuite, TestSuiteFactory
from .test_runner import ITestRunner, TestRunner, FilteredTestRunner, ContinuousTestRunner
from .test_reporter import ITestReporter, TestReporter, SlackReporter


class TestFactory:
    """
    Main factory for creating test framework components
    Single Responsibility: Centralized object creation
    Open/Closed: Easy to extend with new types
    """
    
    @staticmethod
    def create_config(config_file: Optional[str] = None) -> TestConfig:
        """Create test configuration"""
        return TestConfig(config_file)
    
    @staticmethod
    def create_suite(config: TestSuiteConfig, **kwargs) -> ITestSuite:
        """Create test suite"""
        return TestSuiteFactory.create_suite(config, **kwargs)
    
    @staticmethod
    def create_runner(
        config: TestConfig, 
        runner_type: str = "standard",
        **kwargs
    ) -> ITestRunner:
        """Create test runner"""
        reporter = TestFactory.create_reporter(config.reporting)
        
        if runner_type == "standard":
            return TestRunner(config, reporter)
        elif runner_type == "filtered":
            base_runner = TestRunner(config, reporter)
            filters = kwargs.get('filters', {})
            return FilteredTestRunner(base_runner, filters)
        elif runner_type == "continuous":
            base_runner = TestRunner(config, reporter)
            fail_fast = kwargs.get('fail_fast', True)
            return ContinuousTestRunner(base_runner, fail_fast)
        else:
            raise ValueError(f"Unknown runner type: {runner_type}")
    
    @staticmethod
    def create_reporter(
        config: Dict[str, Any], 
        reporter_type: str = "standard"
    ) -> ITestReporter:
        """Create test reporter"""
        if reporter_type == "standard":
            return TestReporter(config)
        elif reporter_type == "slack":
            webhook_url = config.get('slack_webhook_url')
            if not webhook_url:
                raise ValueError("Slack webhook URL required for Slack reporter")
            return SlackReporter(webhook_url, config)
        else:
            raise ValueError(f"Unknown reporter type: {reporter_type}")


class TestSuiteBuilder:
    """
    Builder for creating complex test suite configurations
    Single Responsibility: Build test suite configurations
    """
    
    def __init__(self):
        self._config = {}
        self._dependencies = []
        self._markers = []
    
    def with_name(self, name: str) -> 'TestSuiteBuilder':
        """Set suite name"""
        self._config['name'] = name
        return self
    
    def with_type(self, test_type: TestType) -> 'TestSuiteBuilder':
        """Set test type"""
        self._config['test_type'] = test_type
        return self
    
    def with_priority(self, priority: TestPriority) -> 'TestSuiteBuilder':
        """Set priority"""
        self._config['priority'] = priority
        return self
    
    def with_path(self, path: Path) -> 'TestSuiteBuilder':
        """Set test path"""
        self._config['path'] = path
        return self
    
    def with_pattern(self, pattern: str) -> 'TestSuiteBuilder':
        """Set test pattern"""
        self._config['pattern'] = pattern
        return self
    
    def with_timeout(self, timeout: int) -> 'TestSuiteBuilder':
        """Set timeout"""
        self._config['timeout'] = timeout
        return self
    
    def with_parallel(self, parallel: bool = True) -> 'TestSuiteBuilder':
        """Set parallel execution"""
        self._config['parallel'] = parallel
        return self
    
    def with_coverage(self, coverage: bool = True) -> 'TestSuiteBuilder':
        """Set coverage tracking"""
        self._config['coverage'] = coverage
        return self
    
    def with_dependency(self, dependency: str) -> 'TestSuiteBuilder':
        """Add dependency"""
        self._dependencies.append(dependency)
        return self
    
    def with_dependencies(self, dependencies: List[str]) -> 'TestSuiteBuilder':
        """Add multiple dependencies"""
        self._dependencies.extend(dependencies)
        return self
    
    def with_marker(self, marker: str) -> 'TestSuiteBuilder':
        """Add marker"""
        self._markers.append(marker)
        return self
    
    def with_markers(self, markers: List[str]) -> 'TestSuiteBuilder':
        """Add multiple markers"""
        self._markers.extend(markers)
        return self
    
    def build(self) -> TestSuiteConfig:
        """Build the test suite configuration"""
        # Validate required fields
        required_fields = ['name', 'test_type', 'priority', 'path', 'pattern', 'timeout']
        for field in required_fields:
            if field not in self._config:
                raise ValueError(f"Required field '{field}' not set")
        
        # Set defaults
        self._config.setdefault('parallel', True)
        self._config.setdefault('coverage', True)
        self._config['dependencies'] = self._dependencies
        self._config['markers'] = self._markers
        
        return TestSuiteConfig(**self._config)


class TestEnvironmentFactory:
    """
    Factory for creating test environments
    Single Responsibility: Create test environment setups
    """
    
    @staticmethod
    def create_unit_test_environment() -> Dict[str, Any]:
        """Create environment for unit tests"""
        return {
            'database_enabled': False,
            'external_services_enabled': False,
            'mocking_enabled': True,
            'fixtures_path': Path('tests/fixtures/unit'),
            'temp_dir_cleanup': True
        }
    
    @staticmethod
    def create_integration_test_environment() -> Dict[str, Any]:
        """Create environment for integration tests"""
        return {
            'database_enabled': True,
            'external_services_enabled': True,
            'mocking_enabled': False,
            'fixtures_path': Path('tests/fixtures/integration'),
            'temp_dir_cleanup': True,
            'docker_compose_file': 'docker-compose.test.yml'
        }
    
    @staticmethod
    def create_e2e_test_environment() -> Dict[str, Any]:
        """Create environment for E2E tests"""
        return {
            'database_enabled': True,
            'external_services_enabled': True,
            'browser_enabled': True,
            'mocking_enabled': False,
            'fixtures_path': Path('tests/fixtures/e2e'),
            'temp_dir_cleanup': True,
            'docker_compose_file': 'docker-compose.test.yml',
            'browser_options': {
                'headless': True,
                'window_size': '1920,1080'
            }
        }
    
    @staticmethod
    def create_performance_test_environment() -> Dict[str, Any]:
        """Create environment for performance tests"""
        return {
            'database_enabled': True,
            'external_services_enabled': True,
            'mocking_enabled': False,
            'fixtures_path': Path('tests/fixtures/performance'),
            'temp_dir_cleanup': True,
            'docker_compose_file': 'docker-compose.test.yml',
            'metrics_collection': True,
            'resource_monitoring': True
        }


class TestDataFactory:
    """
    Factory for creating test data
    Single Responsibility: Generate test data objects
    """
    
    @staticmethod
    def create_mock_user(role: str = "student", **kwargs) -> Dict[str, Any]:
        """Create mock user data"""
        from uuid import uuid4
        from datetime import datetime
        
        defaults = {
            'id': str(uuid4()),
            'email': f'test.user.{uuid4().hex[:8]}@example.com',
            'username': f'testuser_{uuid4().hex[:8]}',
            'full_name': 'Test User',
            'role': role,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_mock_course(**kwargs) -> Dict[str, Any]:
        """Create mock course data"""
        from uuid import uuid4
        from datetime import datetime
        
        defaults = {
            'id': str(uuid4()),
            'title': f'Test Course {uuid4().hex[:8]}',
            'description': 'A comprehensive test course for automated testing',
            'instructor_id': str(uuid4()),
            'difficulty': 'beginner',
            'category': 'programming',
            'duration_hours': 40,
            'is_published': False,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'tags': ['test', 'automated']
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_mock_quiz(**kwargs) -> Dict[str, Any]:
        """Create mock quiz data"""
        from uuid import uuid4
        from datetime import datetime
        
        defaults = {
            'id': str(uuid4()),
            'course_id': str(uuid4()),
            'title': f'Test Quiz {uuid4().hex[:8]}',
            'description': 'A test quiz for automated testing',
            'difficulty': 'beginner',
            'time_limit': 30,
            'max_attempts': 3,
            'questions': [
                {
                    'id': str(uuid4()),
                    'question': 'What is the primary purpose of unit testing?',
                    'type': 'multiple_choice',
                    'options': [
                        'To test individual components in isolation',
                        'To test the entire application',
                        'To test user interfaces',
                        'To test database connections'
                    ],
                    'correct_answer': 'To test individual components in isolation',
                    'points': 1
                }
            ],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_mock_lab_environment(**kwargs) -> Dict[str, Any]:
        """Create mock lab environment data"""
        from uuid import uuid4
        from datetime import datetime
        
        defaults = {
            'id': str(uuid4()),
            'course_id': str(uuid4()),
            'name': f'Test Lab {uuid4().hex[:8]}',
            'description': 'A test lab environment for automated testing',
            'language': 'python',
            'template': 'python_basic',
            'resources': {
                'cpu': '1000m',
                'memory': '512Mi',
                'storage': '1Gi'
            },
            'environment_variables': {
                'PYTHON_VERSION': '3.9',
                'WORKSPACE': '/workspace'
            },
            'files': [
                {
                    'name': 'main.py',
                    'content': '# Test lab file\nprint("Hello, Test World!")',
                    'type': 'python'
                }
            ],
            'status': 'active',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults


class TestAssertionFactory:
    """
    Factory for creating custom test assertions
    Single Responsibility: Create reusable test assertions
    """
    
    @staticmethod
    def create_api_response_assertion():
        """Create assertion for API responses"""
        def assert_api_response(response, expected_status=200, expected_keys=None):
            assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"
            
            if expected_keys:
                response_data = response.json()
                for key in expected_keys:
                    assert key in response_data, f"Expected key '{key}' not found in response"
        
        return assert_api_response
    
    @staticmethod
    def create_database_assertion():
        """Create assertion for database operations"""
        def assert_database_record(record, expected_fields=None):
            assert record is not None, "Expected database record, got None"
            
            if expected_fields:
                for field, expected_value in expected_fields.items():
                    actual_value = getattr(record, field, None)
                    assert actual_value == expected_value, f"Expected {field}={expected_value}, got {actual_value}"
        
        return assert_database_record
    
    @staticmethod
    def create_file_assertion():
        """Create assertion for file operations"""
        def assert_file_exists(file_path):
            path = Path(file_path)
            assert path.exists(), f"Expected file {file_path} to exist"
            assert path.is_file(), f"Expected {file_path} to be a file"
        
        return assert_file_exists
    
    @staticmethod
    def create_timing_assertion():
        """Create assertion for timing constraints"""
        def assert_execution_time(func, max_time_seconds):
            import time
            
            start_time = time.time()
            result = func()
            execution_time = time.time() - start_time
            
            assert execution_time <= max_time_seconds, f"Execution took {execution_time:.2f}s, expected <= {max_time_seconds}s"
            return result
        
        return assert_execution_time