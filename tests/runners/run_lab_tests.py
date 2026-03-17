#!/usr/bin/env python3
"""
Comprehensive Test Runner for Lab Container System
Runs all tests and generates detailed reports
"""

import subprocess
import sys
import time
import json
import os
from pathlib import Path
from datetime import datetime
import argparse

class LabTestRunner:
    """Comprehensive test runner for lab container system"""
    
    def __init__(self):
        self.results = {
            "start_time": datetime.utcnow().isoformat(),
            "test_suites": {},
            "summary": {},
            "coverage": {},
            "performance": {}
        }
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        
    def run_all_tests(self, verbose=True, coverage=True):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Lab Container System Test Suite")
        print("=" * 70)
        
        # Test suites to run
        test_suites = [
            {
                "name": "Unit Tests - Lab Manager Service",
                "path": "tests/unit/lab_container/test_lab_manager_service.py",
                "description": "Core lab manager functionality"
            },
            {
                "name": "Integration Tests - Lab Lifecycle",
                "path": "tests/integration/test_lab_lifecycle_integration.py", 
                "description": "Lab lifecycle integration tests"
            },
            {
                "name": "Frontend Tests - Lab Integration",
                "path": "tests/frontend/test_lab_integration_frontend.py",
                "description": "Frontend JavaScript functionality"
            },
            {
                "name": "E2E Tests - Complete Lab System",
                "path": "tests/e2e/test_lab_system_e2e.py",
                "description": "End-to-end user workflows"
            }
        ]
        
        # Run each test suite
        for suite in test_suites:
            print(f"\n📋 Running: {suite['name']}")
            print(f"   Description: {suite['description']}")
            print(f"   Path: {suite['path']}")
            print("-" * 50)
            
            result = self._run_test_suite(suite, verbose, coverage)
            self.results["test_suites"][suite["name"]] = result
            
            # Update totals
            self.total_tests += result.get("total", 0)
            self.passed_tests += result.get("passed", 0)
            self.failed_tests += result.get("failed", 0)
            self.skipped_tests += result.get("skipped", 0)
        
        # Generate final report
        self._generate_final_report()
        
        return self.results
    
    def _run_test_suite(self, suite, verbose=True, coverage=True):
        """Run a single test suite"""
        start_time = time.time()
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            suite["path"],
            "-v" if verbose else "-q",
            "--tb=short",
            "--disable-warnings",
            "-x",  # Stop on first failure for debugging
        ]
        
        if coverage:
            cmd.extend([
                "--cov=lab-containers",
                "--cov-report=term-missing",
                "--cov-report=html:coverage/html_report"
            ])
        
        try:
            # Run the test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            # Parse test results
            output_lines = result.stdout.split('\n')
            test_results = self._parse_pytest_output(output_lines)
            
            # Print results
            if result.returncode == 0:
                print(f"✅ PASSED - {test_results['passed']} tests in {execution_time:.2f}s")
                status = "PASSED"
            else:
                print(f"❌ FAILED - {test_results['failed']} failed, {test_results['passed']} passed in {execution_time:.2f}s")
                status = "FAILED"
                print(f"Error output:\n{result.stderr}")
            
            return {
                "status": status,
                "execution_time": execution_time,
                "total": test_results["total"],
                "passed": test_results["passed"],
                "failed": test_results["failed"],
                "skipped": test_results["skipped"],
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT - Test suite exceeded 5 minute limit")
            return {
                "status": "TIMEOUT",
                "execution_time": 300,
                "total": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "stdout": "",
                "stderr": "Test suite timed out",
                "return_code": -1
            }
            
        except Exception as e:
            print(f"💥 ERROR - {str(e)}")
            return {
                "status": "ERROR",
                "execution_time": time.time() - start_time,
                "total": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }
    
    def _parse_pytest_output(self, output_lines):
        """Parse pytest output to extract test counts"""
        results = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        
        for line in output_lines:
            if "passed" in line and "failed" in line:
                # Extract numbers from summary line
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        try:
                            results["passed"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == "failed":
                        try:
                            results["failed"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == "skipped":
                        try:
                            results["skipped"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
            elif line.startswith("="):
                # Count individual test results
                if "PASSED" in line:
                    results["passed"] += line.count("PASSED")
                elif "FAILED" in line:
                    results["failed"] += line.count("FAILED")
                elif "SKIPPED" in line:
                    results["skipped"] += line.count("SKIPPED")
        
        results["total"] = results["passed"] + results["failed"] + results["skipped"]
        
        # If we couldn't parse properly, estimate from individual test lines
        if results["total"] == 0:
            for line in output_lines:
                if "::" in line and ("PASSED" in line or "FAILED" in line or "SKIPPED" in line):
                    results["total"] += 1
                    if "PASSED" in line:
                        results["passed"] += 1
                    elif "FAILED" in line:
                        results["failed"] += 1
                    elif "SKIPPED" in line:
                        results["skipped"] += 1
        
        return results
    
    def _generate_final_report(self):
        """Generate final test report"""
        self.results["end_time"] = datetime.utcnow().isoformat()
        self.results["summary"] = {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "success_rate": (self.passed_tests / max(self.total_tests, 1)) * 100,
            "total_suites": len(self.results["test_suites"]),
            "passed_suites": sum(1 for suite in self.results["test_suites"].values() if suite["status"] == "PASSED"),
            "failed_suites": sum(1 for suite in self.results["test_suites"].values() if suite["status"] in ["FAILED", "ERROR", "TIMEOUT"])
        }
        
        print("\n" + "=" * 70)
        print("📊 FINAL TEST REPORT")
        print("=" * 70)
        
        # Suite summary
        print(f"Test Suites: {self.results['summary']['passed_suites']}/{self.results['summary']['total_suites']} passed")
        
        # Test summary
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"⏭️  Skipped: {self.skipped_tests}")
        print(f"📈 Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        # Individual suite results
        print("\n📋 Suite Details:")
        for suite_name, result in self.results["test_suites"].items():
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"  {status_icon} {suite_name}: {result['passed']}/{result['total']} tests ({result['execution_time']:.2f}s)")
        
        # Overall result
        overall_success = self.failed_tests == 0 and self.results['summary']['failed_suites'] == 0
        if overall_success:
            print(f"\n🎉 ALL TESTS PASSED! Lab container system is working correctly.")
        else:
            print(f"\n⚠️  Some tests failed. Please review the output above.")
        
        # Save detailed report
        self._save_detailed_report()
        
        return overall_success
    
    def _save_detailed_report(self):
        """Save detailed report to file"""
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON report
        json_report_path = report_dir / f"lab_test_report_{timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # HTML report
        html_report_path = report_dir / f"lab_test_report_{timestamp}.html"
        self._generate_html_report(html_report_path)
        
        print(f"\n📄 Detailed reports saved:")
        print(f"   JSON: {json_report_path}")
        print(f"   HTML: {html_report_path}")
    
    def _generate_html_report(self, output_path):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Lab Container System Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 8px; }}
        .suite {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        .passed {{ background: #d4edda; border-color: #c3e6cb; }}
        .failed {{ background: #f8d7da; border-color: #f5c6cb; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 14px; color: #666; }}
        pre {{ background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Lab Container System Test Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <div class="metric">
            <div class="metric-value">{self.results['summary']['success_rate']:.1f}%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric">
            <div class="metric-value">{self.passed_tests}</div>
            <div class="metric-label">Tests Passed</div>
        </div>
        <div class="metric">
            <div class="metric-value">{self.failed_tests}</div>
            <div class="metric-label">Tests Failed</div>
        </div>
        <div class="metric">
            <div class="metric-value">{self.results['summary']['passed_suites']}/{self.results['summary']['total_suites']}</div>
            <div class="metric-label">Suites Passed</div>
        </div>
    </div>
    
    <h2>📋 Test Suites</h2>
"""
        
        # Add suite details
        for suite_name, result in self.results["test_suites"].items():
            status_class = "passed" if result["status"] == "PASSED" else "failed"
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            
            html_content += f"""
    <div class="suite {status_class}">
        <h3>{status_icon} {suite_name}</h3>
        <p><strong>Status:</strong> {result["status"]}</p>
        <p><strong>Tests:</strong> {result["passed"]}/{result["total"]} passed</p>
        <p><strong>Execution Time:</strong> {result["execution_time"]:.2f}s</p>
        
        {f'<details><summary>Output</summary><pre>{result["stdout"]}</pre></details>' if result["stdout"] else ''}
        {f'<details><summary>Errors</summary><pre>{result["stderr"]}</pre></details>' if result["stderr"] else ''}
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def run_specific_suite(self, suite_name):
        """Run a specific test suite"""
        suite_map = {
            "unit": "tests/unit/lab_container/test_lab_manager_service.py",
            "integration": "tests/integration/test_lab_lifecycle_integration.py",
            "frontend": "tests/frontend/test_lab_integration_frontend.py",
            "e2e": "tests/e2e/test_lab_system_e2e.py"
        }
        
        if suite_name not in suite_map:
            print(f"❌ Unknown test suite: {suite_name}")
            print(f"Available suites: {', '.join(suite_map.keys())}")
            return False
        
        suite = {
            "name": f"{suite_name.title()} Tests",
            "path": suite_map[suite_name],
            "description": f"Running {suite_name} tests only"
        }
        
        print(f"🚀 Running {suite['name']}")
        result = self._run_test_suite(suite, verbose=True, coverage=True)
        
        if result["status"] == "PASSED":
            print(f"✅ {suite_name} tests completed successfully!")
            return True
        else:
            print(f"❌ {suite_name} tests failed!")
            return False


def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description="Lab Container System Test Runner")
    parser.add_argument("--suite", choices=["unit", "integration", "frontend", "e2e"], 
                       help="Run specific test suite only")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    runner = LabTestRunner()
    
    if args.suite:
        # Run specific suite
        success = runner.run_specific_suite(args.suite)
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        results = runner.run_all_tests(
            verbose=not args.quiet,
            coverage=not args.no_coverage
        )
        
        # Exit with appropriate code
        success = results["summary"]["failed_tests"] == 0 and results["summary"]["failed_suites"] == 0
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()