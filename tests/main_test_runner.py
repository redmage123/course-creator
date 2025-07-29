#!/usr/bin/env python3
"""
Main Test Runner for Course Creator Platform
SOLID Principles Implementation:
- Single Responsibility: Orchestrate comprehensive test execution
- Open/Closed: Extensible through configuration and plugins
- Liskov Substitution: Uses interface abstractions throughout
- Interface Segregation: Clean, focused interfaces
- Dependency Inversion: Depends on abstractions, not concretions
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent))

from framework import TestFactory, TestConfig, TestType, TestPriority


async def main():
    """Main entry point for test runner"""
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Starting Course Creator Platform Test Runner")
    logger.info(f"Configuration: {vars(args)}")
    
    try:
        # Create test configuration
        config = TestFactory.create_config(args.config_file)
        
        # Validate configuration
        config_errors = config.validate_config()
        if config_errors:
            logger.error(f"Configuration errors: {config_errors}")
            return 1
        
        # Create appropriate test runner
        runner = create_test_runner(config, args)
        
        # Execute tests based on arguments
        results = await execute_tests(runner, args, logger)
        
        # Print summary
        print_summary(results)
        
        # Determine exit code
        exit_code = determine_exit_code(results)
        logger.info(f"Test runner finished with exit code: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Fatal error in test runner: {e}", exc_info=True)
        return 1


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Course Creator Platform Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_test_runner.py                              # Run all tests
  python main_test_runner.py --type unit                  # Run only unit tests
  python main_test_runner.py --priority high             # Run high priority tests
  python main_test_runner.py --suite user_management_unit # Run specific suite
  python main_test_runner.py --coverage --verbose        # Run with coverage and verbose output
  python main_test_runner.py --ci --fail-fast           # CI mode with fail-fast
        """
    )
    
    # Test selection options
    parser.add_argument(
        '--type', '-t',
        type=str,
        choices=['unit', 'integration', 'frontend', 'e2e', 'security', 'performance'],
        help='Run tests of specific type'
    )
    
    parser.add_argument(
        '--priority', '-p', 
        type=str,
        choices=['high', 'medium', 'low'],
        help='Run tests of specific priority'
    )
    
    parser.add_argument(
        '--suite', '-s',
        type=str,
        help='Run specific test suite'
    )
    
    parser.add_argument(
        '--suites',
        type=str,
        nargs='+',
        help='Run multiple specific test suites'
    )
    
    # Execution options
    parser.add_argument(
        '--parallel', '-j',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Timeout per test suite in seconds (default: 600)'
    )
    
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Disable parallel execution'
    )
    
    # Output options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet output (errors only)'
    )
    
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Generate coverage reports'
    )
    
    parser.add_argument(
        '--no-reports',
        action='store_true',
        help='Skip generating reports'
    )
    
    # CI/CD options
    parser.add_argument(
        '--ci',
        action='store_true',
        help='Run in CI/CD mode'
    )
    
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first failure'
    )
    
    # Configuration
    parser.add_argument(
        '--config-file',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '-- filters',
        nargs='*',
        help='Additional pytest filters'
    )
    
    return parser


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('test_runner.log')
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


def create_test_runner(config: TestConfig, args: argparse.Namespace):
    """Create appropriate test runner based on arguments"""
    if args.ci:
        # Create CI/CD optimized runner
        return TestFactory.create_runner(
            config, 
            runner_type="continuous",
            fail_fast=args.fail_fast
        )
    elif args.type or args.priority or args.suite or args.suites:
        # Create filtered runner
        filters = {}
        
        if args.type:
            filters['type'] = TestType(args.type)
        if args.priority:
            filters['priority'] = TestPriority(args.priority)
        if args.suite:
            filters['suite'] = args.suite
        if args.suites:
            filters['suites'] = args.suites
        
        return TestFactory.create_runner(
            config,
            runner_type="filtered", 
            filters=filters
        )
    else:
        # Create standard runner
        return TestFactory.create_runner(config, runner_type="standard")


async def execute_tests(runner, args: argparse.Namespace, logger) -> Dict[str, Any]:
    """Execute tests based on arguments"""
    if args.suite:
        # Run specific suite
        result = await runner.run_suite(args.suite)
        return {args.suite: result}
    
    elif args.suites:
        # Run multiple specific suites
        results = {}
        for suite_name in args.suites:
            result = await runner.run_suite(suite_name)
            results[suite_name] = result
        return results
    
    elif args.type:
        # Run by type
        test_type = TestType(args.type)
        return await runner.run_by_type(test_type)
    
    elif args.priority:
        # Run by priority
        priority = TestPriority(args.priority)
        return await runner.run_by_priority(priority)
    
    else:
        # Run all tests
        return await runner.run_all()


def print_summary(results: Dict[str, Any]) -> None:
    """Print test execution summary"""
    if not results:
        print("No tests were executed.")
        return
    
    # Calculate summary statistics
    total_suites = len(results)
    passed_suites = len([r for r in results.values() if hasattr(r, 'result') and r.result.value == 'passed'])
    failed_suites = total_suites - passed_suites
    
    total_tests = sum(getattr(r, 'tests_run', 0) for r in results.values())
    passed_tests = sum(getattr(r, 'tests_passed', 0) for r in results.values())
    failed_tests = sum(getattr(r, 'tests_failed', 0) for r in results.values())
    skipped_tests = sum(getattr(r, 'tests_skipped', 0) for r in results.values())
    
    total_time = sum(getattr(r, 'execution_time', 0.0) for r in results.values())
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Print summary
    print("\n" + "=" * 80)
    print("🧪 TEST EXECUTION SUMMARY")
    print("=" * 80)
    
    print(f"📊 Overall Statistics:")
    print(f"   Total Test Suites: {total_suites}")
    print(f"   Passed Suites: {passed_suites} ✅")
    print(f"   Failed Suites: {failed_suites} ❌")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Total Execution Time: {total_time:.2f}s")
    
    print(f"\n🔍 Test Details:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests} ✅")
    print(f"   Failed: {failed_tests} ❌")
    print(f"   Skipped: {skipped_tests} ⏭️")
    
    # Print suite-by-suite results
    print(f"\n📋 Suite Results:")
    for suite_name, result in results.items():
        if hasattr(result, 'result'):
            status_icon = {
                'passed': '✅',
                'failed': '❌',
                'error': '💥',
                'skipped': '⏭️'
            }.get(result.result.value, '❓')
            
            print(f"   {status_icon} {suite_name}")
            if hasattr(result, 'execution_time'):
                print(f"      Duration: {result.execution_time:.2f}s")
            if hasattr(result, 'tests_run') and result.tests_run > 0:
                suite_success_rate = (result.tests_passed / result.tests_run * 100)
                print(f"      Tests: {result.tests_run} | Success: {suite_success_rate:.1f}%")
        else:
            print(f"   ❓ {suite_name} (no result data)")
    
    print("=" * 80)
    
    # Overall status
    if failed_suites == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  Some tests failed. Check the detailed output above.")


def determine_exit_code(results: Dict[str, Any]) -> int:
    """Determine appropriate exit code based on results"""
    if not results:
        return 1  # No tests executed
    
    # Check for failures or errors
    for result in results.values():
        if hasattr(result, 'result') and result.result.value in ['failed', 'error']:
            return 1
    
    return 0  # All tests passed


class TestRunnerPlugin:
    """
    Base class for test runner plugins
    Single Responsibility: Extend test runner functionality
    Open/Closed: Plugins can extend without modifying core
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def before_run(self, runner) -> None:
        """Called before test execution starts"""
        pass
    
    async def after_run(self, runner, results: Dict[str, Any]) -> None:
        """Called after test execution completes"""
        pass
    
    async def before_suite(self, suite_name: str) -> None:
        """Called before each test suite"""
        pass
    
    async def after_suite(self, suite_name: str, result) -> None:
        """Called after each test suite"""
        pass


class SlackNotificationPlugin(TestRunnerPlugin):
    """
    Plugin for sending Slack notifications
    Single Responsibility: Handle Slack notifications
    """
    
    async def after_run(self, runner, results: Dict[str, Any]) -> None:
        """Send results to Slack after test run"""
        if not self.config.get('slack_webhook_url'):
            return
        
        try:
            from framework.test_reporter import SlackReporter
            
            slack_reporter = SlackReporter(
                self.config['slack_webhook_url'],
                self.config
            )
            await slack_reporter.generate_report(results)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to send Slack notification: {e}")


class MetricsCollectionPlugin(TestRunnerPlugin):
    """
    Plugin for collecting test metrics
    Single Responsibility: Collect and store test metrics
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.metrics = []
    
    async def after_suite(self, suite_name: str, result) -> None:
        """Collect metrics after each suite"""
        if hasattr(result, 'execution_time'):
            self.metrics.append({
                'suite_name': suite_name,
                'execution_time': result.execution_time,
                'tests_run': getattr(result, 'tests_run', 0),
                'success_rate': getattr(result, 'success_rate', 0),
                'timestamp': asyncio.get_event_loop().time()
            })
    
    async def after_run(self, runner, results: Dict[str, Any]) -> None:
        """Save collected metrics"""
        metrics_file = Path('test_metrics.json')
        
        try:
            import json
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to save metrics: {e}")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)