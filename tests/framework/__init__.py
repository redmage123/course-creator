"""
Test Framework Package
Modular testing architecture following SOLID principles for Course Creator Platform
"""

from .test_config import TestConfig, TestType, TestPriority, TestSuiteConfig
from .test_suite import (
    ITestSuite, BaseTestSuite, PytestTestSuite, JavaScriptTestSuite, 
    TestSuiteFactory, ParallelTestSuite, DependentTestSuite,
    TestExecutionResult, TestResult
)
from .test_runner import TestRunner
from .test_reporter import TestReporter
from .test_factory import TestFactory

__all__ = [
    'TestConfig',
    'TestType', 
    'TestPriority',
    'TestSuiteConfig',
    'ITestSuite',
    'BaseTestSuite',
    'PytestTestSuite',
    'JavaScriptTestSuite',
    'TestSuiteFactory',
    'ParallelTestSuite',
    'DependentTestSuite',
    'TestExecutionResult',
    'TestResult',
    'TestRunner',
    'TestReporter',
    'TestFactory'
]