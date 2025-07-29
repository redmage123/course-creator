"""
Test Configuration Module
Single Responsibility: Manage test configuration settings
Open/Closed: Extensible configuration system
Interface Segregation: Clean configuration interface
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import os
from pathlib import Path


class TestType(Enum):
    """Test type enumeration"""
    UNIT = "unit"
    INTEGRATION = "integration" 
    FRONTEND = "frontend"
    E2E = "e2e"
    SECURITY = "security"
    PERFORMANCE = "performance"


class TestPriority(Enum):
    """Test priority enumeration"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestEnvironmentConfig:
    """Configuration for test environment"""
    database_url: str
    redis_url: str
    jwt_secret: str
    storage_path: str
    ai_api_key: Optional[str] = None
    log_level: str = "INFO"
    parallel_workers: int = 4
    timeout_seconds: int = 600


@dataclass  
class TestSuiteConfig:
    """Configuration for a test suite"""
    name: str
    test_type: TestType
    priority: TestPriority
    path: Path
    pattern: str
    timeout: int
    parallel: bool = True
    coverage: bool = True
    markers: List[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.markers is None:
            self.markers = []
        if self.dependencies is None:
            self.dependencies = []


class TestConfig:
    """
    Main test configuration class following SOLID principles
    Single Responsibility: Central configuration management
    Open/Closed: Extensible through inheritance and composition
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self._config_file = config_file
        self._environment = self._load_environment_config()
        self._suites = self._load_test_suites()
        self._reporting = self._load_reporting_config()
    
    @property
    def environment(self) -> TestEnvironmentConfig:
        """Get environment configuration"""
        return self._environment
    
    @property
    def suites(self) -> Dict[str, TestSuiteConfig]:
        """Get test suite configurations"""
        return self._suites
    
    @property
    def reporting(self) -> Dict[str, Any]:
        """Get reporting configuration"""
        return self._reporting
    
    def get_suite_config(self, suite_name: str) -> Optional[TestSuiteConfig]:
        """Get configuration for specific test suite"""
        return self._suites.get(suite_name)
    
    def get_suites_by_type(self, test_type: TestType) -> List[TestSuiteConfig]:
        """Get all suites of a specific type"""
        return [
            suite for suite in self._suites.values()
            if suite.test_type == test_type
        ]
    
    def get_suites_by_priority(self, priority: TestPriority) -> List[TestSuiteConfig]:
        """Get all suites of a specific priority"""
        return [
            suite for suite in self._suites.values()  
            if suite.priority == priority
        ]
    
    def _load_environment_config(self) -> TestEnvironmentConfig:
        """Load test environment configuration"""
        return TestEnvironmentConfig(
            database_url=os.getenv(
                'TEST_DATABASE_URL',
                'postgresql://test_user:test_password@localhost:5432/course_creator_test'
            ),
            redis_url=os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1'),
            jwt_secret=os.getenv('TEST_JWT_SECRET', 'test_secret_key_for_testing'),
            storage_path=os.getenv('TEST_STORAGE_PATH', '/tmp/test_storage'),
            ai_api_key=os.getenv('TEST_AI_API_KEY'),
            log_level=os.getenv('TEST_LOG_LEVEL', 'INFO'),
            parallel_workers=int(os.getenv('TEST_PARALLEL_WORKERS', '4')),
            timeout_seconds=int(os.getenv('TEST_TIMEOUT_SECONDS', '600'))
        )
    
    def _load_test_suites(self) -> Dict[str, TestSuiteConfig]:
        """Load test suite configurations"""
        base_path = Path(__file__).parent.parent
        
        suites = {
            # Unit Tests
            'user_management_unit': TestSuiteConfig(
                name='User Management Unit Tests',
                test_type=TestType.UNIT,
                priority=TestPriority.HIGH,
                path=base_path / 'unit' / 'user_management',
                pattern='test_*.py',
                timeout=300,
                markers=['unit', 'user_management']
            ),
            'course_management_unit': TestSuiteConfig(
                name='Course Management Unit Tests',
                test_type=TestType.UNIT,
                priority=TestPriority.HIGH,
                path=base_path / 'unit' / 'course_management',
                pattern='test_*.py',
                timeout=300,
                markers=['unit', 'course_management']
            ),
            'course_generator_unit': TestSuiteConfig(
                name='Course Generator Unit Tests',
                test_type=TestType.UNIT,
                priority=TestPriority.HIGH,
                path=base_path / 'unit' / 'course_generator',
                pattern='test_*.py',
                timeout=300,
                markers=['unit', 'course_generator']
            ),
            'content_management_unit': TestSuiteConfig(
                name='Content Management Unit Tests',
                test_type=TestType.UNIT,
                priority=TestPriority.HIGH,
                path=base_path / 'unit' / 'content_management',
                pattern='test_*.py',
                timeout=300,
                markers=['unit', 'content_management']
            ),
            'analytics_unit': TestSuiteConfig(
                name='Analytics Unit Tests',
                test_type=TestType.UNIT,
                priority=TestPriority.HIGH,
                path=base_path / 'unit' / 'analytics',
                pattern='test_*.py',
                timeout=300,
                markers=['unit', 'analytics']
            ),
            
            # Integration Tests
            'service_integration': TestSuiteConfig(
                name='Service Integration Tests',
                test_type=TestType.INTEGRATION,
                priority=TestPriority.HIGH,
                path=base_path / 'integration' / 'services',
                pattern='test_*.py',
                timeout=600,
                markers=['integration', 'services'],
                dependencies=['user_management_unit', 'course_management_unit']
            ),
            'api_integration': TestSuiteConfig(
                name='API Integration Tests',
                test_type=TestType.INTEGRATION,
                priority=TestPriority.HIGH,
                path=base_path / 'integration' / 'api',
                pattern='test_*.py',
                timeout=600,
                markers=['integration', 'api'],
                dependencies=['service_integration']
            ),
            'database_integration': TestSuiteConfig(
                name='Database Integration Tests',
                test_type=TestType.INTEGRATION,
                priority=TestPriority.MEDIUM,
                path=base_path / 'integration' / 'database',
                pattern='test_*.py',
                timeout=600,
                markers=['integration', 'database']
            ),
            
            # Frontend Tests
            'frontend_components': TestSuiteConfig(
                name='Frontend Component Tests',
                test_type=TestType.FRONTEND,
                priority=TestPriority.HIGH,
                path=base_path / 'frontend' / 'components',
                pattern='test_*.py',
                timeout=300,
                markers=['frontend', 'components']
            ),
            'frontend_integration': TestSuiteConfig(
                name='Frontend Integration Tests',
                test_type=TestType.FRONTEND,
                priority=TestPriority.MEDIUM,
                path=base_path / 'frontend' / 'integration',
                pattern='test_*.py',
                timeout=600,
                markers=['frontend', 'integration'],
                dependencies=['frontend_components']
            ),
            
            # E2E Tests
            'user_workflows': TestSuiteConfig(
                name='User Workflow E2E Tests',
                test_type=TestType.E2E,
                priority=TestPriority.HIGH,
                path=base_path / 'e2e' / 'workflows',
                pattern='test_*.py',
                timeout=900,
                parallel=False,
                markers=['e2e', 'workflows'],
                dependencies=['api_integration', 'frontend_integration']
            ),
            'course_lifecycle': TestSuiteConfig(
                name='Course Lifecycle E2E Tests',
                test_type=TestType.E2E,
                priority=TestPriority.HIGH,
                path=base_path / 'e2e' / 'course_lifecycle',
                pattern='test_*.py',
                timeout=900,
                parallel=False,
                markers=['e2e', 'course_lifecycle'],
                dependencies=['user_workflows']
            ),
            
            # Security Tests
            'authentication_security': TestSuiteConfig(
                name='Authentication Security Tests',
                test_type=TestType.SECURITY,
                priority=TestPriority.HIGH,
                path=base_path / 'security' / 'auth',
                pattern='test_*.py',
                timeout=300,
                markers=['security', 'auth']
            ),
            'data_security': TestSuiteConfig(
                name='Data Security Tests',
                test_type=TestType.SECURITY,
                priority=TestPriority.HIGH,
                path=base_path / 'security' / 'data',
                pattern='test_*.py',
                timeout=300,
                markers=['security', 'data']
            ),
            
            # Performance Tests
            'load_tests': TestSuiteConfig(
                name='Load Performance Tests',
                test_type=TestType.PERFORMANCE,
                priority=TestPriority.MEDIUM,
                path=base_path / 'performance' / 'load',
                pattern='test_*.py',
                timeout=1200,
                parallel=False,
                coverage=False,
                markers=['performance', 'load'],
                dependencies=['api_integration']
            )
        }
        
        return suites
    
    def _load_reporting_config(self) -> Dict[str, Any]:
        """Load reporting configuration"""
        return {
            'formats': ['json', 'html', 'junit'],
            'output_dir': Path(__file__).parent.parent / 'reports',
            'coverage': {
                'enabled': True,
                'threshold': 80,
                'exclude_patterns': ['tests/*', '*/test_*', '*/__pycache__/*'],
                'report_formats': ['html', 'term', 'json']
            },
            'metrics': {
                'track_duration': True,
                'track_memory': True,
                'track_failures': True,
                'generate_trends': True
            }
        }
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []
        
        # Validate environment config
        if not self._environment.database_url:
            errors.append("Database URL is required")
        
        # Validate suite paths
        for suite_name, suite_config in self._suites.items():
            if not suite_config.path.exists():
                errors.append(f"Test suite path does not exist: {suite_config.path}")
        
        # Validate dependencies
        all_suite_names = set(self._suites.keys())
        for suite_name, suite_config in self._suites.items():
            for dep in suite_config.dependencies:
                if dep not in all_suite_names:
                    errors.append(f"Invalid dependency '{dep}' for suite '{suite_name}'")
        
        return errors