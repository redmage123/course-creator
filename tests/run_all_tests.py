#!/usr/bin/env python3
"""
Comprehensive Test Runner for Course Creator Platform
Runs all test suites including unit, integration, e2e, frontend, and specialized tests
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime
import json

# Import specialized test runners
sys.path.append(str(Path(__file__).parent))
try:
    from runners.run_organization_tests import OrganizationTestRunner
except ImportError:
    OrganizationTestRunner = None

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
            cwd=Path(__file__).parent.parent
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

def run_test_suite(suite_name, test_configs, verbose=False, coverage=False):
    """Run a specific test suite"""
    print(f"\n🧪 RUNNING {suite_name.upper()} TESTS")
    print(f"{'='*60}")
    
    results = {}
    total_passed = 0
    total_failed = 0
    
    for test_name, config in test_configs.items():
        # Skip if test path doesn't exist
        test_path = Path(config["path"])
        if not test_path.exists():
            print(f"⚠️  Test path not found: {test_path}")
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
        passed = 0
        failed = 0
        if stdout and "passed" in stdout:
            # Basic parsing of pytest output
            lines = stdout.split('\n')
            for line in lines:
                if "passed" in line and ("failed" in line or "error" in line):
                    try:
                        # Extract numbers from summary line
                        words = line.split()
                        for i, word in enumerate(words):
                            if "passed" in word:
                                passed = int(words[i-1]) if i > 0 else 0
                            elif "failed" in word:
                                failed = int(words[i-1]) if i > 0 else 0
                    except:
                        pass
                elif "passed" in line and "failed" not in line:
                    try:
                        words = line.split()
                        for i, word in enumerate(words):
                            if "passed" in word and i > 0:
                                passed = int(words[i-1])
                    except:
                        pass
        
        total_passed += passed
        total_failed += failed
        
        results[test_name] = {
            "success": success,
            "passed": passed,
            "failed": failed,
            "stdout": stdout,
            "stderr": stderr
        }
    
    return results, total_passed, total_failed

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument(
        "--suite", 
        choices=["unit", "integration", "frontend", "e2e", "security", "content", "lint", "lab", "analytics", "rbac", "organization", "student_login"],
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
        "--no-reports",
        action="store_true",
        help="Skip generating reports"
    )
    
    args = parser.parse_args()
    
    # Test suite configurations
    test_suites = {
        "unit": {
            "services": {
                "path": "tests/unit/services/",
                "command": "python -m pytest tests/unit/services/ -v --tb=short",
                "description": "Unit Tests - Service Layer",
                "timeout": 300
            },
            "backend": {
                "path": "tests/unit/backend/",
                "command": "python -m pytest tests/unit/backend/ -v --tb=short",
                "description": "Unit Tests - Backend Components",
                "timeout": 300
            },
            "lab_container": {
                "path": "tests/unit/lab_container/",
                "command": "python -m pytest tests/unit/lab_container/ -v --tb=short",
                "description": "Unit Tests - Lab Container System",
                "timeout": 300
            },
            "analytics": {
                "path": "tests/unit/analytics/",
                "command": "python -m pytest tests/unit/analytics/ -v --tb=short",
                "description": "Unit Tests - Analytics Service",
                "timeout": 300
            },
            "misc": {
                "path": "tests/unit/",
                "command": "python -m pytest tests/unit/test_*.py -v --tb=short",
                "description": "Unit Tests - Miscellaneous",
                "timeout": 300
            },
            "rbac": {
                "path": "tests/unit/rbac/",
                "command": "python -m pytest tests/unit/rbac/ -v --tb=short",
                "description": "Unit Tests - RBAC System",
                "timeout": 300
            },
            "organization_management": {
                "path": "tests/unit/organization_management/",
                "command": "python -m pytest tests/unit/organization_management/ -v --tb=short",
                "description": "Unit Tests - Organization Management",
                "timeout": 300
            },
            "user_management": {
                "path": "tests/unit/user_management/",
                "command": "python -m pytest tests/unit/user_management/ -v --tb=short",
                "description": "Unit Tests - User Management & Student Login",
                "timeout": 300
            }
        },
        "integration": {
            "api": {
                "path": "tests/integration/",
                "command": "python -m pytest tests/integration/ -v --tb=short",
                "description": "Integration Tests - API and Service Communication",
                "timeout": 600
            },
            "lab": {
                "path": "tests/integration/test_lab_lifecycle_integration.py",
                "command": "python -m pytest tests/integration/test_lab_lifecycle_integration.py -v --tb=short",
                "description": "Integration Tests - Lab Lifecycle",
                "timeout": 600
            },
            "rbac": {
                "path": "tests/integration/test_rbac_api_integration.py",
                "command": "python -m pytest tests/integration/test_rbac_api_integration.py -v --tb=short",
                "description": "Integration Tests - RBAC API",
                "timeout": 600
            },
            "organization_api": {
                "path": "tests/integration/test_organization_api_integration.py",
                "command": "python -m pytest tests/integration/test_organization_api_integration.py -v --tb=short",
                "description": "Integration Tests - Organization API",
                "timeout": 600
            },
            "student_login_gdpr": {
                "path": "tests/integration/test_student_login_gdpr.py",
                "command": "python -m pytest tests/integration/test_student_login_gdpr.py -v --tb=short",
                "description": "Integration Tests - Student Login GDPR Compliance",
                "timeout": 600
            },
            "authentication": {
                "path": "tests/integration/test_authentication_integration.py",
                "command": "python -m pytest tests/integration/test_authentication_integration.py -v --tb=short",
                "description": "Integration Tests - Authentication & JWT Middleware (Login, Password Reset, Token Validation)",
                "timeout": 600
            }
        },
        "frontend": {
            "core": {
                "path": "tests/frontend/",
                "command": "python -m pytest tests/frontend/ -v --tb=short -x",
                "description": "Frontend Tests - JavaScript and UI Components",
                "timeout": 600
            },
            "rbac": {
                "path": "tests/frontend/test_rbac_dashboard_frontend.py",
                "command": "python -m pytest tests/frontend/test_rbac_dashboard_frontend.py -v --tb=short",
                "description": "Frontend Tests - RBAC Dashboard Components",
                "timeout": 600
            },
            "organization_registration": {
                "path": "tests/frontend/test_organization_registration_frontend.js",
                "command": "npx jest tests/frontend/test_organization_registration_frontend.js --verbose",
                "description": "Frontend Tests - Organization Registration JavaScript",
                "timeout": 300
            },
            "platform_comprehensive": {
                "path": "tests/frontend/test_platform_comprehensive.py",
                "command": "python -m pytest tests/frontend/test_platform_comprehensive.py -v --tb=short",
                "description": "Frontend Tests - Comprehensive Platform Validation (HTTPS, Country Dropdowns, Organization Registration)",
                "timeout": 900
            },
            "student_login_ui": {
                "path": "tests/frontend/test_student_login_ui.py",
                "command": "python -m pytest tests/frontend/test_student_login_ui.py -v --tb=short",
                "description": "Frontend Tests - Student Login UI & GDPR Compliance",
                "timeout": 600
            }
        },
        "e2e": {
            "workflows": {
                "path": "tests/e2e/",
                "command": "python -m pytest tests/e2e/ -v --tb=short -s",
                "description": "End-to-End Tests - Complete Workflows",
                "timeout": 900
            },
            "rbac": {
                "path": "tests/e2e/test_rbac_complete_workflows.py",
                "command": "python -m pytest tests/e2e/test_rbac_complete_workflows.py -v --tb=short -s",
                "description": "End-to-End Tests - RBAC Complete Workflows",
                "timeout": 900
            },
            "organization_registration": {
                "path": "tests/e2e/test_organization_registration_e2e.py",
                "command": "python -m pytest tests/e2e/test_organization_registration_e2e.py -v --tb=short -s",
                "description": "End-to-End Tests - Organization Registration Flow",
                "timeout": 900
            },
            "student_login_e2e": {
                "path": "tests/e2e/test_student_login_e2e.py",
                "command": "python -m pytest tests/e2e/test_student_login_e2e.py -v --tb=short -s",
                "description": "End-to-End Tests - Student Login Complete Workflows",
                "timeout": 900
            },
            "critical_instructor_journey": {
                "path": "tests/e2e/critical_user_journeys/test_instructor_complete_journey.py",
                "command": "python -m pytest tests/e2e/critical_user_journeys/test_instructor_complete_journey.py -v --tb=short",
                "description": "End-to-End Tests - Critical Instructor User Journey",
                "timeout": 1200
            },
            "critical_student_journey": {
                "path": "tests/e2e/critical_user_journeys/test_student_complete_journey.py",
                "command": "python -m pytest tests/e2e/critical_user_journeys/test_student_complete_journey.py -v --tb=short",
                "description": "End-to-End Tests - Critical Student User Journey",
                "timeout": 1200
            },
            "org_admin_notifications": {
                "path": "tests/e2e/test_org_admin_notifications_e2e.py",
                "command": "python -m pytest tests/e2e/test_org_admin_notifications_e2e.py -v --tb=short",
                "description": "End-to-End Tests - Org Admin Notifications & Meeting Rooms",
                "timeout": 900
            }
        },
        "security": {
            "auth": {
                "path": "tests/security/",
                "command": "python -m pytest tests/security/ -v --tb=short",
                "description": "Security Tests - Authentication and Authorization",
                "timeout": 300
            }
        },
        "content": {
            "management": {
                "path": "tests/content/",
                "command": "python -m pytest tests/content/ -v --tb=short",
                "description": "Content Tests - File Processing and Management",
                "timeout": 600
            }
        },
        "lint": {
            "student_login": {
                "path": "tests/lint/test_student_login_lint.py",
                "command": "python -m pytest tests/lint/test_student_login_lint.py -v --tb=short",
                "description": "Lint Tests - Student Login Code Quality & GDPR Compliance",
                "timeout": 300
            }
        }
    }
    
    # Specialized test runners
    specialized_runners = {
        "lab": {
            "path": "tests/runners/run_lab_tests.py",
            "command": "python tests/runners/run_lab_tests.py",
            "description": "Lab System Comprehensive Tests"
        },
        "analytics": {
            "path": "tests/runners/run_analytics_tests.py", 
            "command": "python tests/runners/run_analytics_tests.py",
            "description": "Analytics System Comprehensive Tests"
        },
        "rbac": {
            "path": "tests/runners/run_rbac_tests.py",
            "command": "python tests/runners/run_rbac_tests.py",
            "description": "Enhanced RBAC System Comprehensive Tests"
        },
        "organization": {
            "path": "tests/runners/run_organization_tests.py",
            "command": "python tests/runners/run_organization_tests.py",
            "description": "Organization Management Comprehensive Tests (Unit, Integration, E2E, Frontend)"
        },
        "student_login": {
            "path": "tests/runners/run_student_login_tests.py",
            "command": "python tests/runners/run_student_login_tests.py",
            "description": "Student Login System Comprehensive Tests (GDPR-Compliant Authentication, Privacy Controls)"
        }
    }
    
    # Run tests
    start_time = datetime.now()
    report = {
        "start_time": start_time.isoformat(),
        "test_results": {},
        "summary": {},
        "command_args": vars(args)
    }
    
    print(f"""
🧪 COURSE CREATOR PLATFORM TEST RUNNER
======================================
Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
Suite: {args.suite or 'all'}
Verbose: {args.verbose}
Coverage: {args.coverage}
""")
    
    total_passed = 0
    total_failed = 0
    
    # Determine which suites to run
    if args.suite:
        if args.suite in test_suites:
            suites_to_run = {args.suite: test_suites[args.suite]}
        elif args.suite in specialized_runners:
            # Run specialized runner
            config = specialized_runners[args.suite]
            if Path(config["path"]).exists():
                success, stdout, stderr = run_command(
                    config["command"],
                    config["description"],
                    timeout=900
                )
                report["test_results"][args.suite] = {
                    "success": success,
                    "stdout": stdout,
                    "stderr": stderr
                }
            else:
                print(f"⚠️  Specialized runner not found: {config['path']}")
            suites_to_run = {}
        else:
            print(f"❌ Unknown test suite: {args.suite}")
            sys.exit(1)
    else:
        suites_to_run = test_suites
    
    # Run selected test suites
    for suite_name, suite_config in suites_to_run.items():
        results, passed, failed = run_test_suite(
            suite_name, 
            suite_config, 
            verbose=args.verbose,
            coverage=args.coverage
        )
        
        report["test_results"][suite_name] = results
        total_passed += passed
        total_failed += failed
    
    # Run specialized runners if running all tests
    if not args.suite:
        for runner_name, config in specialized_runners.items():
            if Path(config["path"]).exists():
                success, stdout, stderr = run_command(
                    config["command"],
                    config["description"],
                    timeout=900
                )
                report["test_results"][f"specialized_{runner_name}"] = {
                    "success": success,
                    "stdout": stdout,
                    "stderr": stderr
                }
    
    # Generate summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    total_tests = total_passed + total_failed
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    report["summary"] = {
        "end_time": end_time.isoformat(),
        "duration_seconds": duration.total_seconds(),
        "total_tests": total_tests,
        "passed_tests": total_passed,
        "failed_tests": total_failed,
        "success_rate": success_rate,
        "all_passed": total_failed == 0
    }
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Duration: {duration}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed} ✅")
    print(f"Failed: {total_failed} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if report["summary"]["all_passed"]:
        print(f"\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  Some tests failed. Check output above for details.")
    
    # Save report
    if not args.no_reports:
        report_file = Path("test_report_comprehensive.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Full test report saved to: {report_file}")
        
        if args.coverage:
            print(f"📈 Coverage reports generated in htmlcov/ directory")
    
    # Exit with appropriate code
    sys.exit(0 if report["summary"]["all_passed"] else 1)

if __name__ == "__main__":
    main()