"""
Test Runner Module
Single Responsibility: Orchestrate test execution
Open/Closed: Extensible test execution system
Dependency Inversion: Depends on test suite abstractions
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from .test_config import TestConfig, TestType, TestPriority
from .test_suite import (
    ITestSuite, TestSuiteFactory, TestExecutionResult, 
    ParallelTestSuite, DependentTestSuite, TestResult
)
from .test_reporter import TestReporter


class ITestRunner(ABC):
    """
    Interface for test runners following Interface Segregation Principle
    """
    
    @abstractmethod
    async def run_all(self) -> Dict[str, TestExecutionResult]:
        """Run all configured test suites"""
        pass
    
    @abstractmethod
    async def run_suite(self, suite_name: str) -> TestExecutionResult:
        """Run specific test suite"""
        pass
    
    @abstractmethod
    async def run_by_type(self, test_type: TestType) -> Dict[str, TestExecutionResult]:
        """Run all suites of specific type"""
        pass
    
    @abstractmethod
    async def run_by_priority(self, priority: TestPriority) -> Dict[str, TestExecutionResult]:
        """Run all suites of specific priority"""
        pass


class TestRunner(ITestRunner):
    """
    Main test runner implementation following SOLID principles
    Single Responsibility: Orchestrate test execution
    Open/Closed: Extensible through composition
    Dependency Inversion: Depends on abstractions
    """
    
    def __init__(self, config: TestConfig, reporter: Optional[TestReporter] = None):
        self._config = config
        self._reporter = reporter or TestReporter(config.reporting)
        self._logger = logging.getLogger(__name__)
        self._executed_suites: Set[str] = set()
        
    async def run_all(self) -> Dict[str, TestExecutionResult]:
        """Run all configured test suites"""
        self._logger.info("Starting complete test run")
        
        # Validate configuration
        config_errors = self._config.validate_config()
        if config_errors:
            self._logger.error(f"Configuration errors: {config_errors}")
            raise ValueError(f"Configuration errors: {config_errors}")
        
        # Create execution plan
        execution_plan = self._create_execution_plan(list(self._config.suites.keys()))
        
        # Execute all suites according to plan
        results = {}
        for phase in execution_plan:
            phase_results = await self._execute_phase(phase)
            results.update(phase_results)
            
            # Check if we should continue
            if not self._should_continue(phase_results):
                self._logger.warning("Stopping execution due to critical failures")
                break
        
        # Generate report
        await self._reporter.generate_report(results)
        
        self._logger.info("Complete test run finished")
        return results
    
    async def run_suite(self, suite_name: str) -> TestExecutionResult:
        """Run specific test suite"""
        self._logger.info(f"Running test suite: {suite_name}")
        
        suite_config = self._config.get_suite_config(suite_name)
        if not suite_config:
            raise ValueError(f"Test suite '{suite_name}' not found")
        
        # Create and execute suite
        suite = TestSuiteFactory.create_suite(suite_config)
        
        # Handle dependencies
        if suite_config.dependencies:
            dep_suites = []
            for dep_name in suite_config.dependencies:
                if dep_name not in self._executed_suites:
                    dep_result = await self.run_suite(dep_name)
                    if dep_result.result in [TestResult.FAILED, TestResult.ERROR]:
                        self._logger.error(f"Dependency {dep_name} failed, skipping {suite_name}")
                        return TestExecutionResult(
                            suite_name=suite_name,
                            result=TestResult.SKIPPED,
                            tests_run=0,
                            tests_passed=0,
                            tests_failed=0,
                            tests_skipped=1,
                            execution_time=0.0,
                            error_output=f"Dependency {dep_name} failed"
                        )
        
        result = await suite.execute()
        self._executed_suites.add(suite_name)
        
        self._logger.info(f"Test suite {suite_name} completed: {result.result.value}")
        return result
    
    async def run_by_type(self, test_type: TestType) -> Dict[str, TestExecutionResult]:
        """Run all suites of specific type"""
        self._logger.info(f"Running tests of type: {test_type.value}")
        
        suites = self._config.get_suites_by_type(test_type)
        suite_names = [suite.name.lower().replace(' ', '_') for suite in suites]
        
        execution_plan = self._create_execution_plan(suite_names)
        
        results = {}
        for phase in execution_plan:
            phase_results = await self._execute_phase(phase)
            results.update(phase_results)
        
        return results
    
    async def run_by_priority(self, priority: TestPriority) -> Dict[str, TestExecutionResult]:
        """Run all suites of specific priority"""
        self._logger.info(f"Running tests with priority: {priority.value}")
        
        suites = self._config.get_suites_by_priority(priority)
        suite_names = [suite.name.lower().replace(' ', '_') for suite in suites]
        
        execution_plan = self._create_execution_plan(suite_names)
        
        results = {}
        for phase in execution_plan:
            phase_results = await self._execute_phase(phase)
            results.update(phase_results)
        
        return results
    
    def _create_execution_plan(self, suite_names: List[str]) -> List[List[str]]:
        """
        Create execution plan considering dependencies
        Returns list of phases, where each phase contains suites that can run in parallel
        """
        # Build dependency graph
        graph = {}
        in_degree = {}
        
        for suite_name in suite_names:
            suite_config = self._config.get_suite_config(suite_name)
            if not suite_config:
                continue
                
            graph[suite_name] = suite_config.dependencies
            in_degree[suite_name] = 0
        
        # Calculate in-degrees
        for suite_name in suite_names:
            suite_config = self._config.get_suite_config(suite_name)
            if not suite_config:
                continue
                
            for dep in suite_config.dependencies:
                if dep in in_degree:
                    in_degree[suite_name] += 1
        
        # Topological sort to create phases
        phases = []
        remaining = set(suite_names)
        
        while remaining:
            # Find suites with no dependencies
            current_phase = []
            for suite_name in list(remaining):
                if in_degree[suite_name] == 0:
                    current_phase.append(suite_name)
                    remaining.remove(suite_name)
            
            if not current_phase:
                # Circular dependency or invalid dependency
                self._logger.warning("Circular dependency detected, running remaining suites")
                current_phase = list(remaining)
                remaining.clear()
            
            phases.append(current_phase)
            
            # Update in-degrees
            for suite_name in current_phase:
                suite_config = self._config.get_suite_config(suite_name)
                if suite_config:
                    for dependent in suite_names:
                        dep_config = self._config.get_suite_config(dependent)
                        if dep_config and suite_name in dep_config.dependencies:
                            in_degree[dependent] -= 1
        
        return phases
    
    async def _execute_phase(self, suite_names: List[str]) -> Dict[str, TestExecutionResult]:
        """Execute a phase of test suites"""
        self._logger.info(f"Executing phase with suites: {suite_names}")
        
        # Create suites for this phase
        suites = []
        for suite_name in suite_names:
            suite_config = self._config.get_suite_config(suite_name)
            if suite_config:
                suite = TestSuiteFactory.create_suite(suite_config)
                suites.append(suite)
        
        # Determine if we can run in parallel
        can_parallel = all(
            self._config.get_suite_config(name).parallel if self._config.get_suite_config(name) else True
            for name in suite_names
        )
        
        if can_parallel and len(suites) > 1:
            # Run in parallel
            parallel_suite = ParallelTestSuite(
                suites, 
                max_workers=self._config.environment.parallel_workers
            )
            results_list = await parallel_suite.execute()
            
            # Convert to dictionary
            results = {}
            for i, result in enumerate(results_list):
                results[suite_names[i]] = result
        else:
            # Run sequentially
            results = {}
            for i, suite in enumerate(suites):
                result = await suite.execute()
                results[suite_names[i]] = result
                self._executed_suites.add(suite_names[i])
        
        return results
    
    def _should_continue(self, phase_results: Dict[str, TestExecutionResult]) -> bool:
        """Determine if execution should continue based on phase results"""
        critical_failures = 0
        
        for result in phase_results.values():
            if result.result in [TestResult.FAILED, TestResult.ERROR]:
                # Check if this is a high priority suite
                suite_config = None
                for config in self._config.suites.values():
                    if config.name.lower().replace(' ', '_') in phase_results:
                        suite_config = config
                        break
                
                if suite_config and suite_config.priority == TestPriority.HIGH:
                    critical_failures += 1
        
        # Continue if less than 50% of high priority suites failed
        return critical_failures < len(phase_results) * 0.5


class FilteredTestRunner(ITestRunner):
    """
    Test runner with filtering capabilities
    Single Responsibility: Run filtered subset of tests
    """
    
    def __init__(self, base_runner: ITestRunner, filters: Dict[str, Any]):
        self._base_runner = base_runner
        self._filters = filters
    
    async def run_all(self) -> Dict[str, TestExecutionResult]:
        """Run all tests matching filters"""
        # Apply filters and delegate to base runner
        if 'type' in self._filters:
            return await self._base_runner.run_by_type(self._filters['type'])
        elif 'priority' in self._filters:
            return await self._base_runner.run_by_priority(self._filters['priority'])
        else:
            return await self._base_runner.run_all()
    
    async def run_suite(self, suite_name: str) -> TestExecutionResult:
        """Run specific suite if it matches filters"""
        return await self._base_runner.run_suite(suite_name)
    
    async def run_by_type(self, test_type: TestType) -> Dict[str, TestExecutionResult]:
        """Run by type"""
        return await self._base_runner.run_by_type(test_type)
    
    async def run_by_priority(self, priority: TestPriority) -> Dict[str, TestExecutionResult]:
        """Run by priority"""
        return await self._base_runner.run_by_priority(priority)


class ContinuousTestRunner(ITestRunner):
    """
    Test runner for continuous integration
    Single Responsibility: Manage CI/CD test execution
    """
    
    def __init__(self, base_runner: ITestRunner, fail_fast: bool = True):
        self._base_runner = base_runner
        self._fail_fast = fail_fast
    
    async def run_all(self) -> Dict[str, TestExecutionResult]:
        """Run all tests with CI/CD optimizations"""
        # Run high priority tests first
        high_priority_results = await self._base_runner.run_by_priority(TestPriority.HIGH)
        
        if self._fail_fast:
            # Check if any high priority tests failed
            has_failures = any(
                result.result in [TestResult.FAILED, TestResult.ERROR]
                for result in high_priority_results.values()
            )
            
            if has_failures:
                return high_priority_results
        
        # Run remaining tests
        all_results = await self._base_runner.run_all()
        return all_results
    
    async def run_suite(self, suite_name: str) -> TestExecutionResult:
        """Run specific suite"""
        return await self._base_runner.run_suite(suite_name)
    
    async def run_by_type(self, test_type: TestType) -> Dict[str, TestExecutionResult]:
        """Run by type"""
        return await self._base_runner.run_by_type(test_type)
    
    async def run_by_priority(self, priority: TestPriority) -> Dict[str, TestExecutionResult]:
        """Run by priority"""
        return await self._base_runner.run_by_priority(priority)