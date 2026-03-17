#!/usr/bin/env python3
"""
Analytics Test Runner
Comprehensive test runner for the student analytics system
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime
import json

def run_command(command, description, timeout=300):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ SUCCESS ({execution_time:.2f}s)")
            if result.stdout:
                print(f"Output:\n{result.stdout}")
        else:
            print(f"❌ FAILED ({execution_time:.2f}s)")
            print(f"Error output:\n{result.stderr}")
            if result.stdout:
                print(f"Standard output:\n{result.stdout}")
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT after {timeout}s")
        return False, "", "Test timed out"
    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}")
        return False, "", str(e)

def check_services_health():
    """Check if required services are running"""
    print(f"\n{'='*60}")
    print("🏥 Checking Service Health")
    print(f"{'='*60}")
    
    services = [
        ("Analytics Service", "http://localhost:8007/health"),
        ("Course Generator", "http://localhost:8001/health"),
        ("Lab Container Manager", "http://localhost:8006/health"),
    ]
    
    all_healthy = True
    
    try:
        import requests
        
        for service_name, health_url in services:
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name}: Healthy")
                else:
                    print(f"⚠️  {service_name}: Unhealthy (HTTP {response.status_code})")
                    all_healthy = False
            except requests.exceptions.RequestException:
                print(f"❌ {service_name}: Not responding")
                all_healthy = False
                
    except ImportError:
        print("⚠️  requests library not available, skipping health checks")
        return True  # Assume healthy if we can't check
    
    return all_healthy

def run_analytics_tests(test_suite=None, verbose=False, coverage=False):
    """Run analytics test suite"""
    
    # Test report
    report = {
        "start_time": datetime.now().isoformat(),
        "test_results": {},
        "summary": {},
        "services_health": None
    }
    
    print(f"""
🧪 ANALYTICS TEST SUITE RUNNER
================================
Start Time: {report['start_time']}
Test Suite: {test_suite or 'all'}
Verbose: {verbose}
Coverage: {coverage}
""")
    
    # Check service health first
    services_healthy = check_services_health()
    report["services_health"] = services_healthy
    
    if not services_healthy:
        print("\n⚠️  Some services are not healthy. Tests may fail.")
        print("Please ensure all services are running:")
        print("  - Analytics Service (port 8007)")
        print("  - Course Generator (port 8001)")
        print("  - Lab Container Manager (port 8006)")
        print("\nContinuing with tests...")
    
    # Test configurations
    test_suites = {
        "unit": {
            "path": "tests/unit/analytics/",
            "description": "Unit Tests - Analytics Models and Business Logic",
            "command": "python -m pytest tests/unit/analytics/ -v --tb=short"
        },
        "integration": {
            "path": "tests/integration/",
            "description": "Integration Tests - API Endpoints and Service Integration",
            "command": "python -m pytest tests/integration/test_analytics_integration.py -v --tb=short"
        },
        "e2e": {
            "path": "tests/e2e/",
            "description": "End-to-End Tests - Analytics Dashboard UI",
            "command": "python -m pytest tests/e2e/test_analytics_dashboard_e2e.py -v --tb=short -s"
        }
    }
    
    # Add coverage if requested
    if coverage:
        for suite in test_suites.values():
            suite["command"] += f" --cov=services/analytics --cov-report=html:htmlcov_{suite['path'].split('/')[-2]}"
    
    # Add verbose flag if requested
    if verbose:
        for suite in test_suites.values():
            suite["command"] += " -vv"
    
    # Run specific test suite or all
    suites_to_run = [test_suite] if test_suite else list(test_suites.keys())
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for suite_name in suites_to_run:
        if suite_name not in test_suites:
            print(f"❌ Unknown test suite: {suite_name}")
            continue
            
        suite = test_suites[suite_name]
        
        # Check if test files exist
        test_path = Path(suite["path"])
        if not test_path.exists():
            print(f"⚠️  Test path not found: {test_path}")
            continue
        
        # Run the test suite
        success, stdout, stderr = run_command(
            suite["command"],
            suite["description"],
            timeout=600  # 10 minutes for e2e tests
        )
        
        # Parse pytest output for test counts
        if stdout:
            lines = stdout.split('\n')
            for line in lines:
                if 'passed' in line and 'failed' in line:
                    # Parse pytest summary line
                    try:
                        if 'passed' in line:
                            passed = int(line.split()[0])
                            passed_tests += passed
                        if 'failed' in line:
                            failed = int(line.split('failed')[0].split()[-1])
                            failed_tests += failed
                    except:
                        pass
        
        # Store results
        report["test_results"][suite_name] = {
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "description": suite["description"]
        }
    
    # Generate summary
    total_tests = passed_tests + failed_tests
    report["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
        "all_passed": failed_tests == 0
    }
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    
    if report["summary"]["all_passed"]:
        print(f"\n🎉 ALL ANALYTICS TESTS PASSED!")
    else:
        print(f"\n⚠️  Some tests failed. Check output above for details.")
    
    # Save report
    report_file = Path("analytics_test_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Full test report saved to: {report_file}")
    
    if coverage:
        print(f"\n📈 Coverage reports generated in htmlcov_* directories")
    
    return report["summary"]["all_passed"]

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run analytics test suite")
    parser.add_argument(
        "--suite", 
        choices=["unit", "integration", "e2e"],
        help="Run specific test suite (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true", 
        help="Generate coverage reports"
    )
    parser.add_argument(
        "--no-health-check",
        action="store_true",
        help="Skip service health checks"
    )
    
    args = parser.parse_args()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed. Install with: pip install pytest")
        sys.exit(1)
    
    # Run tests
    success = run_analytics_tests(
        test_suite=args.suite,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()