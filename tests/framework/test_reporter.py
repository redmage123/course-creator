"""
Test Reporter Module
Single Responsibility: Generate test reports and metrics
Open/Closed: Extensible reporting system
Interface Segregation: Clean reporting interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import logging

from .test_suite import TestExecutionResult, TestResult


class ITestReporter(ABC):
    """
    Interface for test reporters following Interface Segregation Principle
    """
    
    @abstractmethod
    async def generate_report(self, results: Dict[str, TestExecutionResult]) -> None:
        """Generate test report"""
        pass
    
    @abstractmethod
    async def save_report(self, report_data: Dict[str, Any], format: str) -> Path:
        """Save report in specified format"""
        pass


class TestReporter(ITestReporter):
    """
    Main test reporter implementation following SOLID principles
    Single Responsibility: Generate comprehensive test reports
    Open/Closed: Extensible through format handlers
    """
    
    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._output_dir = Path(config.get('output_dir', 'test_reports'))
        self._output_dir.mkdir(parents=True, exist_ok=True)
        
        # Format handlers following Strategy Pattern
        self._format_handlers = {
            'json': self._generate_json_report,
            'html': self._generate_html_report,
            'junit': self._generate_junit_report,
            'console': self._generate_console_report
        }
    
    async def generate_report(self, results: Dict[str, TestExecutionResult]) -> None:
        """Generate test report in all configured formats"""
        self._logger.info("Generating test reports")
        
        # Generate summary data
        summary = self._generate_summary(results)
        
        # Generate reports in all configured formats
        formats = self._config.get('formats', ['json', 'html'])
        
        for format_name in formats:
            try:
                report_data = {
                    'summary': summary,
                    'results': results,
                    'metadata': self._generate_metadata()
                }
                
                await self.save_report(report_data, format_name)
                self._logger.info(f"Generated {format_name} report")
                
            except Exception as e:
                self._logger.error(f"Failed to generate {format_name} report: {e}")
        
        # Generate coverage report if enabled
        if self._config.get('coverage', {}).get('enabled', False):
            await self._generate_coverage_report(results)
    
    async def save_report(self, report_data: Dict[str, Any], format: str) -> Path:
        """Save report in specified format"""
        handler = self._format_handlers.get(format)
        if not handler:
            raise ValueError(f"Unsupported report format: {format}")
        
        return await handler(report_data)
    
    def _generate_summary(self, results: Dict[str, TestExecutionResult]) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_tests = sum(result.tests_run for result in results.values())
        total_passed = sum(result.tests_passed for result in results.values())
        total_failed = sum(result.tests_failed for result in results.values())
        total_skipped = sum(result.tests_skipped for result in results.values())
        total_time = sum(result.execution_time for result in results.values())
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Suite-level statistics
        suites_passed = len([r for r in results.values() if r.result == TestResult.PASSED])
        suites_failed = len([r for r in results.values() if r.result == TestResult.FAILED])
        suites_error = len([r for r in results.values() if r.result == TestResult.ERROR])
        suites_skipped = len([r for r in results.values() if r.result == TestResult.SKIPPED])
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_suites': len(results),
            'suites_passed': suites_passed,
            'suites_failed': suites_failed,
            'suites_error': suites_error,
            'suites_skipped': suites_skipped,
            'total_tests': total_tests,
            'tests_passed': total_passed,
            'tests_failed': total_failed,
            'tests_skipped': total_skipped,
            'success_rate': round(success_rate, 2),
            'total_execution_time': round(total_time, 2),
            'average_execution_time': round(total_time / len(results) if results else 0, 2),
            'status': 'PASSED' if suites_failed == 0 and suites_error == 0 else 'FAILED'
        }
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate report metadata"""
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'generator': 'Course Creator Test Framework',
            'version': '1.0.0',
            'platform': 'Python',
            'configuration': {
                'output_dir': str(self._output_dir),
                'formats': self._config.get('formats', [])
            }
        }
    
    async def _generate_json_report(self, report_data: Dict[str, Any]) -> Path:
        """Generate JSON report"""
        # Convert TestExecutionResult objects to dictionaries
        serializable_data = self._make_serializable(report_data)
        
        report_file = self._output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(serializable_data, f, indent=2, default=str)
        
        return report_file
    
    async def _generate_html_report(self, report_data: Dict[str, Any]) -> Path:
        """Generate HTML report"""
        summary = report_data['summary']
        results = report_data['results']
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {summary['timestamp']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric h3 {{ margin: 0; color: #495057; }}
        .metric .value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        .error {{ color: #6f42c1; }}
        .suite {{ margin: 15px 0; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; }}
        .suite-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .suite-name {{ font-weight: bold; font-size: 1.1em; }}
        .suite-status {{ padding: 5px 10px; border-radius: 3px; color: white; }}
        .status-passed {{ background-color: #28a745; }}
        .status-failed {{ background-color: #dc3545; }}
        .status-error {{ background-color: #6f42c1; }}
        .status-skipped {{ background-color: #ffc107; color: black; }}
        .suite-details {{ margin-top: 10px; }}
        .detail-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
        .detail-item {{ background-color: #f8f9fa; padding: 8px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Execution Report</h1>
        <p>Generated on: {summary['timestamp']}</p>
        <p>Status: <strong class="{'passed' if summary['status'] == 'PASSED' else 'failed'}">{summary['status']}</strong></p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Suites</h3>
            <div class="value">{summary['total_suites']}</div>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <div class="value {'passed' if summary['success_rate'] >= 90 else 'failed'}">{summary['success_rate']}%</div>
        </div>
        <div class="metric">
            <h3>Total Tests</h3>
            <div class="value">{summary['total_tests']}</div>
        </div>
        <div class="metric">
            <h3>Execution Time</h3>
            <div class="value">{summary['total_execution_time']:.2f}s</div>
        </div>
    </div>
    
    <h2>Test Suite Results</h2>
"""
        
        for suite_name, result in results.items():
            status_class = f"status-{result.result.value}"
            
            html_content += f"""
    <div class="suite">
        <div class="suite-header">
            <div class="suite-name">{result.suite_name}</div>
            <div class="suite-status {status_class}">{result.result.value.upper()}</div>
        </div>
        <div class="suite-details">
            <div class="detail-grid">
                <div class="detail-item">
                    <strong>Tests Run:</strong> {result.tests_run}
                </div>
                <div class="detail-item">
                    <strong>Passed:</strong> <span class="passed">{result.tests_passed}</span>
                </div>
                <div class="detail-item">
                    <strong>Failed:</strong> <span class="failed">{result.tests_failed}</span>
                </div>
                <div class="detail-item">
                    <strong>Skipped:</strong> <span class="skipped">{result.tests_skipped}</span>
                </div>
                <div class="detail-item">
                    <strong>Duration:</strong> {result.execution_time:.2f}s
                </div>
                <div class="detail-item">
                    <strong>Success Rate:</strong> {result.success_rate:.1f}%
                </div>
            </div>
"""
            
            if result.error_output:
                html_content += f"""
            <div style="margin-top: 10px;">
                <strong>Error Output:</strong>
                <pre style="background-color: #f8d7da; padding: 10px; border-radius: 3px; overflow-x: auto;">{result.error_output}</pre>
            </div>
"""
            
            html_content += """
        </div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        report_file = self._output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        return report_file
    
    async def _generate_junit_report(self, report_data: Dict[str, Any]) -> Path:
        """Generate JUnit XML report"""
        summary = report_data['summary']
        results = report_data['results']
        
        # Create root testsuites element
        testsuites = ET.Element('testsuites')
        testsuites.set('name', 'Course Creator Tests')
        testsuites.set('tests', str(summary['total_tests']))
        testsuites.set('failures', str(summary['tests_failed']))
        testsuites.set('errors', str(len([r for r in results.values() if r.result == TestResult.ERROR])))
        testsuites.set('time', str(summary['total_execution_time']))
        testsuites.set('timestamp', summary['timestamp'])
        
        # Add each test suite
        for suite_name, result in results.items():
            testsuite = ET.SubElement(testsuites, 'testsuite')
            testsuite.set('name', result.suite_name)
            testsuite.set('tests', str(result.tests_run))
            testsuite.set('failures', str(result.tests_failed))
            testsuite.set('errors', '1' if result.result == TestResult.ERROR else '0')
            testsuite.set('skipped', str(result.tests_skipped))
            testsuite.set('time', str(result.execution_time))
            
            # Add a test case (simplified - in real implementation would have individual test cases)
            testcase = ET.SubElement(testsuite, 'testcase')
            testcase.set('name', f"{suite_name}_execution")
            testcase.set('classname', result.suite_name)
            testcase.set('time', str(result.execution_time))
            
            if result.result == TestResult.FAILED:
                failure = ET.SubElement(testcase, 'failure')
                failure.set('message', 'Test suite failed')
                failure.text = result.error_output
            elif result.result == TestResult.ERROR:
                error = ET.SubElement(testcase, 'error')
                error.set('message', 'Test suite error')
                error.text = result.error_output
            elif result.result == TestResult.SKIPPED:
                ET.SubElement(testcase, 'skipped')
        
        # Write XML to file
        report_file = self._output_dir / f"junit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        
        tree = ET.ElementTree(testsuites)
        tree.write(report_file, encoding='utf-8', xml_declaration=True)
        
        return report_file
    
    async def _generate_console_report(self, report_data: Dict[str, Any]) -> Path:
        """Generate console-friendly report"""
        summary = report_data['summary']
        results = report_data['results']
        
        console_output = []
        console_output.append("=" * 80)
        console_output.append("TEST EXECUTION REPORT")
        console_output.append("=" * 80)
        console_output.append(f"Generated: {summary['timestamp']}")
        console_output.append(f"Status: {summary['status']}")
        console_output.append(f"Success Rate: {summary['success_rate']}%")
        console_output.append(f"Total Execution Time: {summary['total_execution_time']:.2f}s")
        console_output.append("")
        
        console_output.append("SUMMARY")
        console_output.append("-" * 40)
        console_output.append(f"Total Suites: {summary['total_suites']}")
        console_output.append(f"  Passed: {summary['suites_passed']}")
        console_output.append(f"  Failed: {summary['suites_failed']}")
        console_output.append(f"  Error: {summary['suites_error']}")
        console_output.append(f"  Skipped: {summary['suites_skipped']}")
        console_output.append("")
        console_output.append(f"Total Tests: {summary['total_tests']}")
        console_output.append(f"  Passed: {summary['tests_passed']}")
        console_output.append(f"  Failed: {summary['tests_failed']}")
        console_output.append(f"  Skipped: {summary['tests_skipped']}")
        console_output.append("")
        
        console_output.append("SUITE DETAILS")
        console_output.append("-" * 40)
        
        for suite_name, result in results.items():
            status_icon = {
                TestResult.PASSED: "✅",
                TestResult.FAILED: "❌", 
                TestResult.ERROR: "💥",
                TestResult.SKIPPED: "⏭️"
            }.get(result.result, "❓")
            
            console_output.append(f"{status_icon} {result.suite_name}")
            console_output.append(f"   Duration: {result.execution_time:.2f}s")
            console_output.append(f"   Tests: {result.tests_run} | Passed: {result.tests_passed} | Failed: {result.tests_failed} | Skipped: {result.tests_skipped}")
            
            if result.error_output:
                console_output.append(f"   Error: {result.error_output[:100]}...")
            
            console_output.append("")
        
        console_output.append("=" * 80)
        
        # Save to file
        report_file = self._output_dir / f"console_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w') as f:
            f.write('\n'.join(console_output))
        
        # Also print to console
        print('\n'.join(console_output))
        
        return report_file
    
    async def _generate_coverage_report(self, results: Dict[str, TestExecutionResult]) -> None:
        """Generate coverage report if coverage data is available"""
        coverage_config = self._config.get('coverage', {})
        
        if not coverage_config.get('enabled', False):
            return
        
        # Calculate overall coverage
        coverage_values = [
            result.coverage for result in results.values() 
            if result.coverage is not None
        ]
        
        if coverage_values:
            overall_coverage = sum(coverage_values) / len(coverage_values)
            threshold = coverage_config.get('threshold', 80)
            
            self._logger.info(f"Overall test coverage: {overall_coverage:.2f}%")
            
            if overall_coverage < threshold:
                self._logger.warning(f"Coverage {overall_coverage:.2f}% is below threshold {threshold}%")
    
    def _make_serializable(self, data: Any) -> Any:
        """Convert data to JSON-serializable format"""
        if isinstance(data, dict):
            return {key: self._make_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        elif isinstance(data, TestExecutionResult):
            return {
                'suite_name': data.suite_name,
                'result': data.result.value,
                'tests_run': data.tests_run,
                'tests_passed': data.tests_passed,
                'tests_failed': data.tests_failed,
                'tests_skipped': data.tests_skipped,
                'execution_time': data.execution_time,
                'success_rate': data.success_rate,
                'coverage': data.coverage,
                'output': data.output,
                'error_output': data.error_output,
                'details': data.details
            }
        elif hasattr(data, '__dict__'):
            return self._make_serializable(data.__dict__)
        else:
            return data


class SlackReporter(ITestReporter):
    """
    Slack notification reporter
    Single Responsibility: Send test results to Slack
    """
    
    def __init__(self, webhook_url: str, config: Dict[str, Any]):
        self._webhook_url = webhook_url
        self._config = config
        self._logger = logging.getLogger(__name__)
    
    async def generate_report(self, results: Dict[str, TestExecutionResult]) -> None:
        """Send test results to Slack"""
        try:
            import aiohttp
            
            # Generate summary
            total_suites = len(results)
            passed_suites = len([r for r in results.values() if r.result == TestResult.PASSED])
            
            # Create Slack message
            color = "good" if passed_suites == total_suites else "danger"
            
            message = {
                "attachments": [
                    {
                        "color": color,
                        "title": "Test Execution Report",
                        "fields": [
                            {
                                "title": "Status",
                                "value": "✅ PASSED" if passed_suites == total_suites else "❌ FAILED",
                                "short": True
                            },
                            {
                                "title": "Suites",
                                "value": f"{passed_suites}/{total_suites} passed",
                                "short": True
                            }
                        ],
                        "footer": "Course Creator Test Framework",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(self._webhook_url, json=message) as response:
                    if response.status == 200:
                        self._logger.info("Successfully sent test results to Slack")
                    else:
                        self._logger.error(f"Failed to send to Slack: {response.status}")
                        
        except Exception as e:
            self._logger.error(f"Error sending Slack notification: {e}")
    
    async def save_report(self, report_data: Dict[str, Any], format: str) -> Path:
        """Not implemented for Slack reporter"""
        raise NotImplementedError("Slack reporter does not save files")