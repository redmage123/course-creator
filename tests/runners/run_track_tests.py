"""
Comprehensive Test Runner for Track System
Runs all track-related tests with detailed reporting
"""
import pytest
import sys
import os
from pathlib import Path
import json
from datetime import datetime


class TrackTestRunner:
    """Comprehensive test runner for track system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_suites": {},
            "summary": {}
        }
    
    def run_unit_tests(self):
        """Run unit tests for track system"""
        print("🧪 Running Track System Unit Tests...")
        
        unit_test_files = [
            "tests/unit/organization_management/test_track_entity.py",
            "tests/unit/organization_management/test_track_repository.py", 
            "tests/unit/organization_management/test_track_service.py"
        ]
        
        results = {}
        for test_file in unit_test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                print(f"  Running {test_file}...")
                result = pytest.main([str(test_path), "-v", "--tb=short"])
                results[test_file] = {
                    "exit_code": result,
                    "status": "PASSED" if result == 0 else "FAILED"
                }
            else:
                print(f"  ⚠️  Test file not found: {test_file}")
                results[test_file] = {
                    "exit_code": -1,
                    "status": "NOT_FOUND"
                }
        
        self.test_results["test_suites"]["unit_tests"] = results
        return results
    
    def run_integration_tests(self):
        """Run integration tests for track system"""
        print("\n🔗 Running Track System Integration Tests...")
        
        integration_test_files = [
            "tests/integration/test_track_system_integration.py"
        ]
        
        results = {}
        for test_file in integration_test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                print(f"  Running {test_file}...")
                result = pytest.main([str(test_path), "-v", "--tb=short"])
                results[test_file] = {
                    "exit_code": result,
                    "status": "PASSED" if result == 0 else "FAILED"
                }
            else:
                print(f"  ⚠️  Test file not found: {test_file}")
                results[test_file] = {
                    "exit_code": -1,
                    "status": "NOT_FOUND"
                }
        
        self.test_results["test_suites"]["integration_tests"] = results
        return results
    
    def run_e2e_tests(self):
        """Run end-to-end tests for track system"""
        print("\n🌐 Running Track System E2E Tests...")
        
        e2e_test_files = [
            "tests/e2e/test_track_system_e2e.py"
        ]
        
        results = {}
        for test_file in e2e_test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                print(f"  Running {test_file}...")
                result = pytest.main([str(test_path), "-v", "--tb=short"])
                results[test_file] = {
                    "exit_code": result,
                    "status": "PASSED" if result == 0 else "FAILED"
                }
            else:
                print(f"  ⚠️  Test file not found: {test_file}")
                results[test_file] = {
                    "exit_code": -1,
                    "status": "NOT_FOUND"
                }
        
        self.test_results["test_suites"]["e2e_tests"] = results
        return results
    
    def run_with_coverage(self):
        """Run all tests with coverage reporting"""
        print("\n📊 Running Track System Tests with Coverage...")
        
        coverage_args = [
            "--cov=services/organization-management/domain/entities/track",
            "--cov=services/organization-management/infrastructure/repositories/postgresql_track_repository",
            "--cov=services/organization-management/application/services/track_service",
            "--cov-report=html:test_reports/track_coverage_html",
            "--cov-report=json:test_reports/track_coverage.json",
            "--cov-report=term",
            "--cov-branch"
        ]
        
        # Run all track tests with coverage
        test_files = [
            "tests/unit/organization_management/test_track_entity.py",
            "tests/unit/organization_management/test_track_repository.py",
            "tests/unit/organization_management/test_track_service.py",
            "tests/integration/test_track_system_integration.py"
        ]
        
        existing_files = [str(self.project_root / f) for f in test_files 
                         if (self.project_root / f).exists()]
        
        if existing_files:
            result = pytest.main(existing_files + coverage_args + ["-v"])
            self.test_results["coverage"] = {
                "exit_code": result,
                "status": "PASSED" if result == 0 else "FAILED"
            }
            return result
        else:
            print("  ⚠️  No test files found for coverage analysis")
            return -1
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n📋 Track System Test Summary")
        print("=" * 50)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for suite_name, suite_results in self.test_results["test_suites"].items():
            print(f"\n{suite_name.upper().replace('_', ' ')}:")
            
            for test_file, result in suite_results.items():
                status_emoji = "✅" if result["status"] == "PASSED" else "❌"
                if result["status"] == "NOT_FOUND":
                    status_emoji = "⚠️"
                
                print(f"  {status_emoji} {test_file}: {result['status']}")
                
                if result["status"] in ["PASSED", "FAILED"]:
                    total_tests += 1
                    if result["status"] == "PASSED":
                        passed_tests += 1
                    else:
                        failed_tests += 1
        
        # Overall summary
        print(f"\n📊 OVERALL RESULTS:")
        print(f"  Total Test Suites: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        
        # Coverage info
        if "coverage" in self.test_results:
            coverage_status = self.test_results["coverage"]["status"]
            coverage_emoji = "✅" if coverage_status == "PASSED" else "❌"
            print(f"  {coverage_emoji} Coverage Analysis: {coverage_status}")
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        return self.test_results
    
    def save_results(self, filename="test_reports/track_test_results.json"):
        """Save test results to file"""
        results_path = self.project_root / filename
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Test results saved to: {results_path}")
    
    def run_all_tests(self, with_coverage=False):
        """Run all track system tests"""
        print("🚀 Starting Comprehensive Track System Testing")
        print("=" * 60)
        
        # Run test suites
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_e2e_tests()
        
        # Run with coverage if requested
        if with_coverage:
            self.run_with_coverage()
        
        # Generate summary
        results = self.generate_summary()
        
        # Save results
        self.save_results()
        
        # Return overall success
        return results["summary"]["failed_tests"] == 0


def main():
    """Main test runner entry point"""
    runner = TrackTestRunner()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Run track system tests")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run only E2E tests")
    
    args = parser.parse_args()
    
    if args.unit:
        runner.run_unit_tests()
        runner.generate_summary()
    elif args.integration:
        runner.run_integration_tests()
        runner.generate_summary()
    elif args.e2e:
        runner.run_e2e_tests()
        runner.generate_summary()
    else:
        # Run all tests
        success = runner.run_all_tests(with_coverage=args.coverage)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()