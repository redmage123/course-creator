"""
Test Suite Module
Single Responsibility: Manage individual test suite execution
Open/Closed: Extensible test suite system
Liskov Substitution: Consistent test suite interface
Interface Segregation: Clean test suite interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import subprocess
import time
import pytest
from pathlib import Path

from .test_config import TestSuiteConfig, TestType


class TestResult(Enum):
    """Test result enumeration"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestExecutionResult:
    """Result of test execution"""
    suite_name: str
    result: TestResult
    tests_run: int
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    execution_time: float
    coverage: Optional[float] = None
    output: str = ""
    error_output: str = ""
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.tests_run == 0:
            return 0.0
        return (self.tests_passed / self.tests_run) * 100


class ITestSuite(ABC):
    """
    Interface for test suites following Interface Segregation Principle
    """
    
    @abstractmethod
    async def setup(self) -> None:
        """Setup test suite"""
        pass
    
    @abstractmethod
    async def execute(self) -> TestExecutionResult:
        """Execute test suite"""
        pass
    
    @abstractmethod
    async def teardown(self) -> None:
        """Teardown test suite"""
        pass
    
    @abstractmethod
    def get_config(self) -> TestSuiteConfig:
        """Get test suite configuration"""
        pass


class BaseTestSuite(ITestSuite):
    """
    Base test suite implementation following SOLID principles
    Single Responsibility: Base test suite functionality
    Open/Closed: Extensible through inheritance
    """
    
    def __init__(self, config: TestSuiteConfig, verbose: bool = False):
        self._config = config
        self._verbose = verbose
        self._setup_complete = False
        self._teardown_complete = False
        
    def get_config(self) -> TestSuiteConfig:
        """Get test suite configuration"""
        return self._config
    
    async def setup(self) -> None:
        """Setup test suite"""
        if self._setup_complete:
            return
            
        await self._perform_setup()
        self._setup_complete = True
    
    async def teardown(self) -> None:
        """Teardown test suite"""
        if self._teardown_complete:
            return
            
        await self._perform_teardown()
        self._teardown_complete = True
    
    async def execute(self) -> TestExecutionResult:
        """Execute test suite"""
        if not self._setup_complete:
            await self.setup()
        
        start_time = time.time()
        
        try:
            result = await self._execute_tests()
            result.execution_time = time.time() - start_time
            return result
        except Exception as e:
            return TestExecutionResult(
                suite_name=self._config.name,
                result=TestResult.ERROR,
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                execution_time=time.time() - start_time,
                error_output=str(e)
            )
        finally:
            await self.teardown()
    
    async def _perform_setup(self) -> None:
        """Perform suite-specific setup"""
        # Create output directories if needed
        if not self._config.path.exists():
            self._config.path.mkdir(parents=True, exist_ok=True)
    
    async def _perform_teardown(self) -> None:
        """Perform suite-specific teardown"""
        # Cleanup temporary files, close connections, etc.
        pass
    
    @abstractmethod
    async def _execute_tests(self) -> TestExecutionResult:
        """Execute the actual tests - to be implemented by subclasses"""
        pass


class PytestTestSuite(BaseTestSuite):
    """
    Pytest-based test suite implementation
    Single Responsibility: Execute pytest-based tests
    """
    
    def __init__(self, config: TestSuiteConfig, verbose: bool = False, coverage: bool = True):
        super().__init__(config, verbose)
        self._coverage = coverage
    
    async def _execute_tests(self) -> TestExecutionResult:
        """Execute pytest tests"""
        # Build pytest command
        args = [
            '--tb=short',
            '--disable-warnings',
            f'--timeout={self._config.timeout}',
        ]
        
        if self._verbose:
            args.append('-vv')
        else:
            args.append('-v')
        
        if self._coverage and self._config.coverage:
            args.extend([
                '--cov=services',
                '--cov=lab-containers', 
                '--cov-report=term-missing',
                '--cov-report=json'
            ])
        
        # Add markers
        if self._config.markers:
            for marker in self._config.markers:
                args.append(f'-m {marker}')
        
        # Add test path
        test_path = str(self._config.path)
        if self._config.pattern != 'test_*.py':
            test_path = f"{test_path}/{self._config.pattern}"
        
        args.append(test_path)
        
        try:
            # Run pytest
            result = pytest.main(args)
            
            # Parse pytest results (simplified parsing)
            # In real implementation, would use pytest plugins for detailed results
            if result == 0:
                return TestExecutionResult(
                    suite_name=self._config.name,
                    result=TestResult.PASSED,
                    tests_run=1,  # Placeholder - would be parsed from pytest output
                    tests_passed=1,
                    tests_failed=0,
                    tests_skipped=0,
                    execution_time=0.0,  # Set by parent execute method
                    output="Tests passed"
                )
            else:
                return TestExecutionResult(
                    suite_name=self._config.name,
                    result=TestResult.FAILED,
                    tests_run=1,
                    tests_passed=0,
                    tests_failed=1,
                    tests_skipped=0,
                    execution_time=0.0,
                    error_output="Tests failed"
                )
                
        except Exception as e:
            return TestExecutionResult(
                suite_name=self._config.name,
                result=TestResult.ERROR,
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                execution_time=0.0,
                error_output=str(e)
            )


class JavaScriptTestSuite(BaseTestSuite):
    """
    JavaScript test suite implementation using Jest/npm test
    Single Responsibility: Execute JavaScript/frontend tests
    """
    
    async def _execute_tests(self) -> TestExecutionResult:
        """Execute JavaScript tests"""
        cmd = ['npm', 'test', '--', '--testPathPattern', str(self._config.path)]
        
        if self._verbose:
            cmd.append('--verbose')
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._config.timeout,
                cwd=Path(__file__).parent.parent.parent
            )
            
            if result.returncode == 0:
                return TestExecutionResult(
                    suite_name=self._config.name,
                    result=TestResult.PASSED,
                    tests_run=1,  # Would parse from Jest output
                    tests_passed=1,
                    tests_failed=0,
                    tests_skipped=0,
                    execution_time=0.0,
                    output=result.stdout
                )
            else:
                return TestExecutionResult(
                    suite_name=self._config.name,
                    result=TestResult.FAILED,
                    tests_run=1,
                    tests_passed=0,
                    tests_failed=1,
                    tests_skipped=0,
                    execution_time=0.0,
                    error_output=result.stderr,
                    output=result.stdout
                )
                
        except subprocess.TimeoutExpired:
            return TestExecutionResult(
                suite_name=self._config.name,
                result=TestResult.ERROR,
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                execution_time=0.0,
                error_output="Test execution timed out"
            )
        except Exception as e:
            return TestExecutionResult(
                suite_name=self._config.name,
                result=TestResult.ERROR,
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                execution_time=0.0,
                error_output=str(e)
            )


class TestSuiteFactory:
    """
    Factory for creating test suites following Factory Pattern
    Single Responsibility: Create appropriate test suite instances
    Open/Closed: Easy to add new test suite types
    """
    
    @staticmethod
    def create_suite(config: TestSuiteConfig, **kwargs) -> ITestSuite:
        """Create test suite based on configuration"""
        if config.test_type in [TestType.UNIT, TestType.INTEGRATION, TestType.E2E, TestType.SECURITY]:
            return PytestTestSuite(config, **kwargs)
        elif config.test_type == TestType.FRONTEND:
            # Check if this is a JavaScript test
            if any(pattern in str(config.path) for pattern in ['js', 'javascript', 'frontend']):
                # Could have both JavaScript and Python frontend tests
                return PytestTestSuite(config, **kwargs)  # For now, use pytest for all
            else:
                return PytestTestSuite(config, **kwargs)
        else:
            return PytestTestSuite(config, **kwargs)


class ParallelTestSuite(ITestSuite):
    """
    Wrapper for running test suites in parallel
    Single Responsibility: Manage parallel test execution
    """
    
    def __init__(self, suites: List[ITestSuite], max_workers: int = 4):
        self._suites = suites
        self._max_workers = max_workers
    
    async def setup(self) -> None:
        """Setup all test suites"""
        for suite in self._suites:
            await suite.setup()
    
    async def teardown(self) -> None:
        """Teardown all test suites"""
        for suite in self._suites:
            await suite.teardown()
    
    async def execute(self) -> List[TestExecutionResult]:
        """Execute all test suites in parallel"""
        import asyncio
        
        # Create semaphore to limit concurrent execution
        semaphore = asyncio.Semaphore(self._max_workers)
        
        async def execute_with_semaphore(suite: ITestSuite) -> TestExecutionResult:
            async with semaphore:
                return await suite.execute()
        
        # Execute all suites concurrently
        tasks = [execute_with_semaphore(suite) for suite in self._suites]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(TestExecutionResult(
                    suite_name=self._suites[i].get_config().name,
                    result=TestResult.ERROR,
                    tests_run=0,
                    tests_passed=0,
                    tests_failed=0,
                    tests_skipped=0,
                    execution_time=0.0,
                    error_output=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_config(self) -> List[TestSuiteConfig]:
        """Get configurations for all suites"""
        return [suite.get_config() for suite in self._suites]


class DependentTestSuite(ITestSuite):
    """
    Test suite that handles dependencies
    Single Responsibility: Manage test suite dependencies
    """
    
    def __init__(self, suite: ITestSuite, dependencies: List[ITestSuite]):
        self._suite = suite
        self._dependencies = dependencies
    
    async def setup(self) -> None:
        """Setup dependencies first, then this suite"""
        for dep in self._dependencies:
            await dep.setup()
        await self._suite.setup()
    
    async def teardown(self) -> None:
        """Teardown this suite, then dependencies"""
        await self._suite.teardown()
        for dep in reversed(self._dependencies):
            await dep.teardown()
    
    async def execute(self) -> TestExecutionResult:
        """Execute dependencies first, then this suite if all pass"""
        # Execute dependencies
        for dep in self._dependencies:
            dep_result = await dep.execute()
            if dep_result.result in [TestResult.FAILED, TestResult.ERROR]:
                return TestExecutionResult(
                    suite_name=self.get_config().name,
                    result=TestResult.FAILED,
                    tests_run=0,
                    tests_passed=0,
                    tests_failed=0,
                    tests_skipped=1,
                    execution_time=0.0,
                    error_output=f"Dependency {dep.get_config().name} failed"
                )
        
        # Execute this suite
        return await self._suite.execute()
    
    def get_config(self) -> TestSuiteConfig:
        """Get this suite's configuration"""
        return self._suite.get_config()