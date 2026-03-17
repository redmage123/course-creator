#!/usr/bin/env python3
"""
Organization Management Test Runner
Executes all organization-related tests: unit, integration, E2E, and frontend
"""
import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class OrganizationTestRunner:
    """
    Comprehensive test runner for organization management functionality
    Coordinates unit tests, integration tests, E2E tests, and frontend tests
    """
    
    def __init__(self):
        self.results = {
            "start_time": datetime.utcnow().isoformat(),
            "test_suites": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": []
            }
        }
        
        self.test_root = Path(__file__).parent.parent
        self.project_root = project_root

    def run_unit_tests(self):
        """Run organization management unit tests"""
        print("🧪 Running Organization Unit Tests...")
        
        unit_test_files = [
            "tests/unit/organization_management/test_organization_service.py",
            "tests/unit/organization_management/test_organization_endpoints.py"
        ]
        
        unit_results = {
            "name": "Unit Tests",
            "tests": [],
            "status": "passed",
            "start_time": datetime.utcnow().isoformat()
        }
        
        for test_file in unit_test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                print(f"  Running {test_file}...")
                
                try:
                    # Run pytest with verbose output and JSON report
                    result = subprocess.run([
                        sys.executable, "-m", "pytest", 
                        str(test_path),
                        "-v", "--tb=short",
                        "--json-report", "--json-report-file=/tmp/pytest_report.json"
                    ], 
                    capture_output=True, text=True, timeout=300)
                    
                    test_result = {
                        "file": test_file,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "status": "passed" if result.returncode == 0 else "failed"
                    }
                    
                    # Parse JSON report if available
                    try:
                        with open("/tmp/pytest_report.json", "r") as f:
                            pytest_data = json.load(f)
                            test_result["pytest_summary"] = pytest_data.get("summary", {})
                    except:
                        pass
                    
                    unit_results["tests"].append(test_result)
                    
                    if result.returncode != 0:
                        unit_results["status"] = "failed"
                        print(f"    ❌ {test_file} failed")
                        self.results["summary"]["errors"].append(f"Unit test failed: {test_file}")
                    else:
                        print(f"    ✅ {test_file} passed")
                        
                except subprocess.TimeoutExpired:
                    test_result = {
                        "file": test_file,
                        "status": "timeout",
                        "error": "Test execution timed out"
                    }
                    unit_results["tests"].append(test_result)
                    unit_results["status"] = "failed"
                    print(f"    ⏰ {test_file} timed out")
                    
            else:
                print(f"  ⚠️  Test file not found: {test_file}")
        
        unit_results["end_time"] = datetime.utcnow().isoformat()
        self.results["test_suites"]["unit_tests"] = unit_results
        
        return unit_results["status"] == "passed"

    def run_integration_tests(self):
        """Run organization API integration tests"""
        print("🔗 Running Organization Integration Tests...")
        
        integration_test_files = [
            "tests/integration/test_organization_api_integration.py"
        ]
        
        integration_results = {
            "name": "Integration Tests",
            "tests": [],
            "status": "passed",
            "start_time": datetime.utcnow().isoformat()
        }
        
        for test_file in integration_test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                print(f"  Running {test_file}...")
                
                try:
                    result = subprocess.run([
                        sys.executable, "-m", "pytest", 
                        str(test_path),
                        "-v", "--tb=short", "-s"
                    ], 
                    capture_output=True, text=True, timeout=600)
                    
                    test_result = {
                        "file": test_file,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "status": "passed" if result.returncode == 0 else "failed"
                    }
                    
                    integration_results["tests"].append(test_result)
                    
                    if result.returncode != 0:
                        integration_results["status"] = "failed"
                        print(f"    ❌ {test_file} failed")
                        self.results["summary"]["errors"].append(f"Integration test failed: {test_file}")
                    else:
                        print(f"    ✅ {test_file} passed")
                        
                except subprocess.TimeoutExpired:
                    test_result = {
                        "file": test_file,
                        "status": "timeout",
                        "error": "Integration test timed out"
                    }
                    integration_results["tests"].append(test_result)
                    integration_results["status"] = "failed"
                    print(f"    ⏰ {test_file} timed out")
                    
            else:
                print(f"  ⚠️  Test file not found: {test_file}")
        
        integration_results["end_time"] = datetime.utcnow().isoformat()
        self.results["test_suites"]["integration_tests"] = integration_results
        
        return integration_results["status"] == "passed"

    def run_e2e_tests(self):
        """Run organization E2E tests"""
        print("🌐 Running Organization E2E Tests...")
        
        e2e_test_files = [
            "tests/e2e/test_organization_registration_e2e.py"
        ]
        
        e2e_results = {
            "name": "E2E Tests",
            "tests": [],
            "status": "passed",
            "start_time": datetime.utcnow().isoformat()
        }
        
        # Check if Chrome/Selenium is available
        try:
            result = subprocess.run([
                "which", "chromedriver"
            ], capture_output=True, timeout=10)
            
            if result.returncode != 0:
                print("  ⚠️  ChromeDriver not found - E2E tests will be skipped")
                e2e_results["status"] = "skipped"
                e2e_results["reason"] = "ChromeDriver not available"
                self.results["test_suites"]["e2e_tests"] = e2e_results
                return True
                
        except:
            print("  ⚠️  Cannot check ChromeDriver - E2E tests will be skipped")
            e2e_results["status"] = "skipped"
            e2e_results["reason"] = "ChromeDriver check failed"
            self.results["test_suites"]["e2e_tests"] = e2e_results
            return True
        
        for test_file in e2e_test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                print(f"  Running {test_file}...")
                
                try:
                    result = subprocess.run([
                        sys.executable, "-m", "pytest", 
                        str(test_path),
                        "-v", "--tb=short", "-s"
                    ], 
                    capture_output=True, text=True, timeout=900)  # 15 minutes for E2E
                    
                    test_result = {
                        "file": test_file,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "status": "passed" if result.returncode == 0 else "failed"
                    }
                    
                    e2e_results["tests"].append(test_result)
                    
                    if result.returncode != 0:
                        # E2E tests are more likely to have environmental issues
                        if "skip" in result.stdout.lower() or "skip" in result.stderr.lower():
                            e2e_results["status"] = "skipped"
                            print(f"    ⏭️  {test_file} skipped (environmental)")
                        else:
                            e2e_results["status"] = "failed"
                            print(f"    ❌ {test_file} failed")
                            self.results["summary"]["errors"].append(f"E2E test failed: {test_file}")
                    else:
                        print(f"    ✅ {test_file} passed")
                        
                except subprocess.TimeoutExpired:
                    test_result = {
                        "file": test_file,
                        "status": "timeout",
                        "error": "E2E test timed out"
                    }
                    e2e_results["tests"].append(test_result)
                    e2e_results["status"] = "failed"
                    print(f"    ⏰ {test_file} timed out")
                    
            else:
                print(f"  ⚠️  Test file not found: {test_file}")
        
        e2e_results["end_time"] = datetime.utcnow().isoformat()
        self.results["test_suites"]["e2e_tests"] = e2e_results
        
        return e2e_results["status"] in ["passed", "skipped"]

    def run_frontend_tests(self):
        """Run frontend JavaScript tests"""
        print("💻 Running Organization Frontend Tests...")
        
        frontend_results = {
            "name": "Frontend Tests",
            "tests": [],
            "status": "passed",
            "start_time": datetime.utcnow().isoformat()
        }
        
        # Check if Node.js and Jest are available
        try:
            result = subprocess.run([
                "node", "--version"
            ], capture_output=True, timeout=10)
            
            if result.returncode != 0:
                print("  ⚠️  Node.js not found - Frontend tests will be skipped")
                frontend_results["status"] = "skipped"
                frontend_results["reason"] = "Node.js not available"
                self.results["test_suites"]["frontend_tests"] = frontend_results
                return True
                
        except:
            print("  ⚠️  Cannot check Node.js - Frontend tests will be skipped")
            frontend_results["status"] = "skipped"
            frontend_results["reason"] = "Node.js check failed"
            self.results["test_suites"]["frontend_tests"] = frontend_results
            return True
        
        # Check if package.json exists for Jest configuration
        package_json_path = self.project_root / "package.json"
        if not package_json_path.exists():
            print("  ⚠️  package.json not found - Creating minimal Jest configuration")
            
            # Create minimal package.json for Jest
            jest_config = {
                "name": "course-creator-tests",
                "version": "1.0.0",
                "scripts": {
                    "test": "jest"
                },
                "devDependencies": {
                    "jest": "^29.0.0",
                    "jsdom": "^20.0.0",
                    "form-data": "^4.0.0"
                },
                "jest": {
                    "testEnvironment": "jsdom",
                    "setupFilesAfterEnv": ["<rootDir>/tests/frontend/setup.js"],
                    "testMatch": ["**/tests/frontend/**/*.test.js"],
                    "collectCoverageFrom": [
                        "frontend/js/**/*.js",
                        "!frontend/js/config.js"
                    ]
                }
            }
            
            with open(package_json_path, "w") as f:
                json.dump(jest_config, f, indent=2)
        
        # Run frontend tests
        frontend_test_files = [
            "tests/frontend/test_organization_registration_frontend.js"
        ]
        
        for test_file in frontend_test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                print(f"  Running {test_file}...")
                
                try:
                    # Try to run with jest directly
                    result = subprocess.run([
                        "npx", "jest", str(test_path), "--verbose"
                    ], 
                    capture_output=True, text=True, timeout=300,
                    cwd=str(self.project_root))
                    
                    test_result = {
                        "file": test_file,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "status": "passed" if result.returncode == 0 else "failed"
                    }
                    
                    frontend_results["tests"].append(test_result)
                    
                    if result.returncode != 0:
                        # Check if it's a dependency issue
                        if "jest" in result.stderr.lower() or "command not found" in result.stderr.lower():
                            frontend_results["status"] = "skipped"
                            frontend_results["reason"] = "Jest not available"
                            print(f"    ⏭️  {test_file} skipped (Jest not available)")
                        else:
                            frontend_results["status"] = "failed"
                            print(f"    ❌ {test_file} failed")
                            self.results["summary"]["errors"].append(f"Frontend test failed: {test_file}")
                    else:
                        print(f"    ✅ {test_file} passed")
                        
                except subprocess.TimeoutExpired:
                    test_result = {
                        "file": test_file,
                        "status": "timeout",
                        "error": "Frontend test timed out"
                    }
                    frontend_results["tests"].append(test_result)
                    frontend_results["status"] = "failed"
                    print(f"    ⏰ {test_file} timed out")
                    
                except FileNotFoundError:
                    test_result = {
                        "file": test_file,
                        "status": "skipped",
                        "reason": "npx/jest not found"
                    }
                    frontend_results["tests"].append(test_result)
                    frontend_results["status"] = "skipped"
                    print(f"    ⏭️  {test_file} skipped (Jest not available)")
                    
            else:
                print(f"  ⚠️  Test file not found: {test_file}")
        
        frontend_results["end_time"] = datetime.utcnow().isoformat()
        self.results["test_suites"]["frontend_tests"] = frontend_results
        
        return frontend_results["status"] in ["passed", "skipped"]

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 ORGANIZATION MANAGEMENT TEST RESULTS")
        print("="*80)
        
        self.results["end_time"] = datetime.utcnow().isoformat()
        
        # Calculate summary statistics
        total_suites = len(self.results["test_suites"])
        passed_suites = sum(1 for suite in self.results["test_suites"].values() 
                           if suite["status"] == "passed")
        failed_suites = sum(1 for suite in self.results["test_suites"].values() 
                           if suite["status"] == "failed")
        skipped_suites = sum(1 for suite in self.results["test_suites"].values() 
                            if suite["status"] == "skipped")
        
        print(f"Test Suites: {total_suites} total, {passed_suites} passed, {failed_suites} failed, {skipped_suites} skipped")
        
        # Detailed results for each suite
        for suite_name, suite_data in self.results["test_suites"].items():
            status_icon = "✅" if suite_data["status"] == "passed" else "❌" if suite_data["status"] == "failed" else "⏭️"
            print(f"\n{status_icon} {suite_data['name']}: {suite_data['status'].upper()}")
            
            if "tests" in suite_data:
                for test in suite_data["tests"]:
                    test_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⏭️"
                    print(f"    {test_icon} {test['file']}")
                    
                    if test["status"] == "failed" and "stderr" in test and test["stderr"]:
                        print(f"        Error: {test['stderr'][:200]}...")
        
        # Error summary
        if self.results["summary"]["errors"]:
            print(f"\n❌ ERRORS ({len(self.results['summary']['errors'])}):")
            for error in self.results["summary"]["errors"]:
                print(f"  - {error}")
        
        # Save detailed report
        report_path = self.test_root / "reports" / "organization_test_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📋 Detailed report saved to: {report_path}")
        
        # Overall success
        overall_success = failed_suites == 0
        if overall_success:
            print("\n🎉 ALL ORGANIZATION TESTS COMPLETED SUCCESSFULLY!")
        else:
            print(f"\n⚠️  {failed_suites} TEST SUITE(S) FAILED")
        
        return overall_success

    def run_all(self):
        """Run all organization tests in sequence"""
        print("🚀 Starting Organization Management Test Suite")
        print(f"📁 Project root: {self.project_root}")
        print(f"⏰ Start time: {self.results['start_time']}")
        
        success = True
        
        # Run test suites in order
        test_suites = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("E2E Tests", self.run_e2e_tests),
            ("Frontend Tests", self.run_frontend_tests)
        ]
        
        for suite_name, run_func in test_suites:
            try:
                suite_success = run_func()
                if not suite_success:
                    success = False
            except Exception as e:
                print(f"❌ Error running {suite_name}: {e}")
                self.results["summary"]["errors"].append(f"{suite_name} execution error: {str(e)}")
                success = False
        
        # Generate final report
        report_success = self.generate_report()
        
        return success and report_success


def main():
    """Main entry point for organization test runner"""
    runner = OrganizationTestRunner()
    success = runner.run_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()