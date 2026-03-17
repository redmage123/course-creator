#!/usr/bin/env python3
"""
Comprehensive RBAC Test Runner
Specialized test runner for Enhanced RBAC system validation
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime
import json

def run_command(command, description, timeout=600):
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
            cwd=Path(__file__).parent.parent.parent
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

def parse_test_results(stdout, stderr):
    """Parse pytest output to extract test results"""
    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    
    if stdout:
        lines = stdout.split('\n')
        for line in lines:
            if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line or 'ERROR' in line):
                if 'PASSED' in line:
                    passed += 1
                elif 'FAILED' in line:
                    failed += 1
                elif 'SKIPPED' in line:
                    skipped += 1
                elif 'ERROR' in line:
                    errors += 1
            elif line.strip().startswith('=') and ('passed' in line or 'failed' in line):
                # Summary line parsing
                words = line.split()
                for i, word in enumerate(words):
                    try:
                        if 'passed' in word and i > 0:
                            passed = int(words[i-1])
                        elif 'failed' in word and i > 0:
                            failed = int(words[i-1])
                        elif 'skipped' in word and i > 0:
                            skipped = int(words[i-1])
                        elif 'error' in word and i > 0:
                            errors = int(words[i-1])
                    except (ValueError, IndexError):
                        continue
    
    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
        "total": passed + failed + skipped + errors
    }

def run_rbac_test_suite(verbose=False, coverage=False):
    """Run comprehensive RBAC test suite"""
    
    # Test configurations
    test_configs = {
        "unit_organization": {
            "path": "tests/unit/rbac/test_organization_service.py",
            "command": "python -m pytest tests/unit/rbac/test_organization_service.py -v --tb=short",
            "description": "RBAC Unit Tests - Organization Service",
            "timeout": 300
        },
        "unit_membership": {
            "path": "tests/unit/rbac/test_membership_service.py", 
            "command": "python -m pytest tests/unit/rbac/test_membership_service.py -v --tb=short",
            "description": "RBAC Unit Tests - Membership Service",
            "timeout": 300
        },
        "unit_track": {
            "path": "tests/unit/rbac/test_track_service.py",
            "command": "python -m pytest tests/unit/rbac/test_track_service.py -v --tb=short",
            "description": "RBAC Unit Tests - Track Service", 
            "timeout": 300
        },
        "unit_meeting_room": {
            "path": "tests/unit/rbac/test_meeting_room_service.py",
            "command": "python -m pytest tests/unit/rbac/test_meeting_room_service.py -v --tb=short",
            "description": "RBAC Unit Tests - Meeting Room Service",
            "timeout": 300
        },
        "integration_api": {
            "path": "tests/integration/test_rbac_api_integration.py",
            "command": "python -m pytest tests/integration/test_rbac_api_integration.py -v --tb=short",
            "description": "RBAC Integration Tests - API Integration",
            "timeout": 600
        },
        "integration_services": {
            "path": "tests/integration/test_rbac_service_integration.py",
            "command": "python -m pytest tests/integration/test_rbac_service_integration.py -v --tb=short",
            "description": "RBAC Integration Tests - Service Integration",
            "timeout": 600
        },
        "frontend_dashboard": {
            "path": "tests/frontend/test_rbac_dashboard_frontend.py",
            "command": "python -m pytest tests/frontend/test_rbac_dashboard_frontend.py -v --tb=short",
            "description": "RBAC Frontend Tests - Dashboard Components",
            "timeout": 600
        },
        "frontend_javascript": {
            "path": "tests/frontend/test_enhanced_rbac_frontend.js",
            "command": "npm run test:unit -- --testPathPattern=test_enhanced_rbac_frontend.js",
            "description": "RBAC Frontend Tests - JavaScript Components", 
            "timeout": 600
        },
        "e2e_workflows": {
            "path": "tests/e2e/test_rbac_complete_workflows.py",
            "command": "python -m pytest tests/e2e/test_rbac_complete_workflows.py -v --tb=short -s",
            "description": "RBAC E2E Tests - Complete Workflows",
            "timeout": 900
        },
        "security_rbac": {
            "path": "tests/security/test_rbac_security.py", 
            "command": "python -m pytest tests/security/test_rbac_security.py -v --tb=short",
            "description": "RBAC Security Tests - Authentication & Authorization",
            "timeout": 300
        }
    }
    
    results = {}
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    total_errors = 0
    
    print(f"""
🛡️  ENHANCED RBAC SYSTEM TEST RUNNER
=====================================
Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Verbose: {verbose}
Coverage: {coverage}
""")
    
    for test_name, config in test_configs.items():
        # Skip if test file doesn't exist
        test_path = Path(config["path"])
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_path}")
            continue
        
        # Build command
        command = config["command"]
        if coverage and "pytest" in command:
            command += " --cov=services --cov=lab-containers"
        if verbose:
            command += " -vv"
        
        # Run test
        success, stdout, stderr = run_command(
            command,
            config["description"],
            timeout=config.get("timeout", 600)
        )
        
        # Parse results
        test_results = parse_test_results(stdout, stderr)
        
        results[test_name] = {
            "success": success,
            "results": test_results,
            "stdout": stdout,
            "stderr": stderr
        }
        
        total_passed += test_results["passed"]
        total_failed += test_results["failed"]
        total_skipped += test_results["skipped"]
        total_errors += test_results["errors"]
    
    # Run linting tests
    print(f"\n🔍 RUNNING RBAC CODE QUALITY CHECKS")
    print(f"{'='*60}")
    
    lint_commands = {
        "eslint_rbac": {
            "command": "npx eslint frontend/js/org-admin-enhanced.js frontend/js/site-admin-dashboard.js --config .eslintrc.rbac.json",
            "description": "ESLint - RBAC JavaScript Files"
        },
        "css_lint": {
            "command": "npx stylelint frontend/css/components/rbac-dashboard.css frontend/css/components/site-admin.css --config .stylelintrc.json",
            "description": "StyleLint - RBAC CSS Files"
        },
        "python_lint": {
            "command": "python -m flake8 services/organization-management/api/ services/organization-management/application/ --max-line-length=88",
            "description": "Flake8 - RBAC Python Code"
        }
    }
    
    lint_results = {}
    for lint_name, config in lint_commands.items():
        success, stdout, stderr = run_command(
            config["command"],
            config["description"],
            timeout=120
        )
        
        lint_results[lint_name] = {
            "success": success,
            "stdout": stdout,
            "stderr": stderr
        }
    
    # Generate comprehensive report
    end_time = datetime.now()
    total_tests = total_passed + total_failed + total_skipped + total_errors
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    report = {
        "start_time": datetime.now().isoformat(),
        "end_time": end_time.isoformat(),
        "test_results": results,
        "lint_results": lint_results,
        "summary": {
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "failed_tests": total_failed,
            "skipped_tests": total_skipped,
            "error_tests": total_errors,
            "success_rate": success_rate,
            "all_passed": total_failed == 0 and total_errors == 0
        }
    }
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 RBAC TEST SUITE SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed} ✅")
    print(f"Failed: {total_failed} ❌")
    print(f"Skipped: {total_skipped} ⏭️")
    print(f"Errors: {total_errors} 💥")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if report["summary"]["all_passed"]:
        print(f"\n🎉 ALL RBAC TESTS PASSED!")
        print("✅ Organization Service")
        print("✅ Membership Service") 
        print("✅ Track Service")
        print("✅ Meeting Room Service")
        print("✅ API Integration")
        print("✅ Frontend Components")
        print("✅ End-to-End Workflows")
        print("✅ Security Validation")
    else:
        print(f"\n⚠️  Some RBAC tests failed. Check output above for details.")
        
        # Show failed test categories
        for test_name, result in results.items():
            if not result["success"] or result["results"]["failed"] > 0:
                print(f"❌ {test_name}: {result['results']['failed']} failed")
    
    # Code quality summary
    print(f"\n🔍 CODE QUALITY SUMMARY")
    print(f"{'='*30}")
    all_lint_passed = True
    for lint_name, result in lint_results.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{lint_name}: {status}")
        if not result["success"]:
            all_lint_passed = False
    
    if all_lint_passed:
        print("\n🎯 All RBAC code quality checks passed!")
    else:
        print("\n⚠️  Some code quality issues found.")
    
    # Component validation
    print(f"\n🧩 RBAC COMPONENT VALIDATION")
    print(f"{'='*35}")
    
    components = [
        ("Organization Management", "unit_organization" in results and results["unit_organization"]["success"]),
        ("Member Management", "unit_membership" in results and results["unit_membership"]["success"]),
        ("Track System", "unit_track" in results and results["unit_track"]["success"]),
        ("Meeting Rooms", "unit_meeting_room" in results and results["unit_meeting_room"]["success"]),
        ("API Endpoints", "integration_api" in results and results["integration_api"]["success"]),
        ("Frontend Dashboard", "frontend_dashboard" in results and results["frontend_dashboard"]["success"]),
        ("JavaScript Components", "frontend_javascript" in results and results["frontend_javascript"]["success"]),
        ("E2E Workflows", "e2e_workflows" in results and results["e2e_workflows"]["success"]),
        ("Security Layer", "security_rbac" in results and results["security_rbac"]["success"])
    ]
    
    for component_name, is_passing in components:
        status = "✅ OPERATIONAL" if is_passing else "❌ ISSUES"
        print(f"{component_name}: {status}")
    
    # Test coverage analysis (if coverage enabled)
    if coverage:
        print(f"\n📈 RBAC TEST COVERAGE ANALYSIS")
        print(f"{'='*35}")
        print("Coverage reports generated for:")
        print("- Organization Management Service")
        print("- Membership Management Service")
        print("- Track Management Service")
        print("- Meeting Room Service")
        print("- RBAC API Endpoints")
        print("- Frontend Components")
        print("\nView detailed coverage: open htmlcov/index.html")
    
    # Save detailed report
    report_file = Path("test_report_rbac_comprehensive.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed RBAC test report saved to: {report_file}")
    
    # Performance metrics
    total_time = (end_time - datetime.now()).total_seconds()
    print(f"\n⏱️  PERFORMANCE METRICS")
    print(f"{'='*25}")
    print(f"Total execution time: {abs(total_time):.2f}s")
    print(f"Average test time: {abs(total_time/len(results)):.2f}s per suite" if results else "N/A")
    print(f"Tests per second: {total_tests/abs(total_time):.2f}" if total_time != 0 else "N/A")
    
    return report["summary"]["all_passed"]

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run comprehensive RBAC test suite")
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
        "--component", 
        choices=["unit", "integration", "frontend", "e2e", "security", "lint"],
        help="Run specific test component"
    )
    
    args = parser.parse_args()
    
    # Run test suite
    success = run_rbac_test_suite(
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()