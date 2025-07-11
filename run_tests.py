#!/usr/bin/env python3
"""
Comprehensive test runner for Course Creator Platform
Runs all test suites with proper environment setup and reporting
"""
import subprocess
import sys
import os
import time
import argparse
from pathlib import Path

class TestRunner:
    """Test runner for the course creator platform"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        
    def run_command(self, command, description, timeout=300):
        """Run a command and capture results"""
        print(f"\n{'='*60}")
        print(f"🧪 {description}")
        print(f"{'='*60}")
        print(f"Command: {' '.join(command)}")
        print()
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            print(f"Exit code: {result.returncode}")
            print(f"Execution time: {execution_time:.2f}s")
            
            if result.stdout:
                print(f"\nSTDOUT:\n{result.stdout}")
                
            if result.stderr:
                print(f"\nSTDERR:\n{result.stderr}")
            
            success = result.returncode == 0
            self.test_results[description] = {
                'success': success,
                'exit_code': result.returncode,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            if success:
                print(f"✅ {description} - PASSED")
            else:
                print(f"❌ {description} - FAILED")
                
            return success
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} - TIMEOUT (>{timeout}s)")
            self.test_results[description] = {
                'success': False,
                'exit_code': -1,
                'execution_time': timeout,
                'error': 'timeout'
            }
            return False
            
        except Exception as e:
            print(f"💥 {description} - ERROR: {e}")
            self.test_results[description] = {
                'success': False,
                'exit_code': -1,
                'execution_time': 0,
                'error': str(e)
            }
            return False
    
    def check_environment(self):
        """Check if environment is properly set up"""
        print("🔍 Checking test environment...")
        
        # Check if virtual environment is activated
        if not os.environ.get('VIRTUAL_ENV'):
            print("⚠️  Virtual environment not detected. Activating...")
            # This script should be run with activated venv
            
        # Check if required packages are installed
        required_packages = ['pytest', 'pytest-asyncio', 'pytest-cov']
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"✅ {package} is installed")
            except ImportError:
                print(f"❌ {package} is NOT installed")
                return False
        
        return True
    
    def run_unit_tests(self):
        """Run unit tests"""
        return self.run_command(
            ['python', '-m', 'pytest', 'tests/unit/', '-v', '--tb=short'],
            "Unit Tests",
            timeout=300
        )
    
    def run_integration_tests(self):
        """Run integration tests"""
        return self.run_command(
            ['python', '-m', 'pytest', 'tests/integration/', '-v', '--tb=short'],
            "Integration Tests",
            timeout=600
        )
    
    def run_security_tests(self):
        """Run security tests"""
        return self.run_command(
            ['python', '-m', 'pytest', 'tests/security/', '-v', '--tb=short'],
            "Security Tests",
            timeout=300
        )
    
    def run_api_tests(self):
        """Run API tests (requires services to be running)"""
        return self.run_command(
            ['python', '-m', 'pytest', 'tests/integration/test_api_workflow_integration.py', '-v', '--tb=short'],
            "API Integration Tests",
            timeout=600
        )
    
    def run_content_generation_tests(self):
        """Run content generation specific tests"""
        return self.run_command(
            ['python', '-m', 'pytest', 'tests/unit/backend/test_content_generation.py', '-v', '--tb=short'],
            "Content Generation Tests",
            timeout=300
        )
    
    def run_session_management_tests(self):
        """Run session management tests"""
        return self.run_command(
            ['python', '-m', 'pytest', 'tests/unit/backend/test_session_management.py', '-v', '--tb=short'],
            "Session Management Tests",
            timeout=300
        )
    
    def run_e2e_tests(self):
        """Run end-to-end tests (requires full platform running)"""
        return self.run_command(
            ['npx', 'playwright', 'test', 'tests/e2e/', '--reporter=html'],
            "End-to-End Tests",
            timeout=900
        )
    
    def run_coverage_report(self):
        """Generate comprehensive coverage report"""
        return self.run_command(
            ['python', '-m', 'pytest', '--cov=services', '--cov-report=html', '--cov-report=term'],
            "Coverage Report Generation",
            timeout=300
        )
    
    def run_performance_tests(self):
        """Run performance tests"""
        # Test our custom content generation performance
        return self.run_command(
            ['python', 'test_content_generation.py'],
            "Performance Tests",
            timeout=120
        )
    
    def check_services_health(self):
        """Check if all services are running"""
        services = [
            ('User Management', 'http://localhost:8000/health'),
            ('Course Generator', 'http://localhost:8001/health'),
            ('Content Storage', 'http://localhost:8003/health'),
            ('Course Management', 'http://localhost:8004/health'),
            ('Frontend', 'http://localhost:3000')
        ]
        
        try:
            import requests
            
            all_healthy = True
            for name, url in services:
                try:
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        print(f"✅ {name} - Healthy")
                    else:
                        print(f"⚠️  {name} - Unhealthy (status: {response.status_code})")
                        all_healthy = False
                except:
                    print(f"❌ {name} - Not responding")
                    all_healthy = False
            
            return all_healthy
            
        except ImportError:
            print("⚠️  requests not available for service health checks")
            return False
    
    def print_summary(self):
        """Print test execution summary"""
        print(f"\n{'='*80}")
        print("📊 TEST EXECUTION SUMMARY")
        print(f"{'='*80}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Test Suites: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if total_tests > 0:
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        else:
            print("Success Rate: N/A (no tests run)")
        print()
        
        # Detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            time_str = f"{result['execution_time']:.2f}s"
            print(f"{status:12} {test_name:40} ({time_str})")
        
        print(f"\n{'='*80}")
        
        if failed_tests > 0:
            print("❌ Some tests failed. Check the output above for details.")
            return False
        else:
            print("🎉 All tests passed successfully!")
            return True

def main():
    parser = argparse.ArgumentParser(description='Run Course Creator Platform tests')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--security', action='store_true', help='Run security tests only')
    parser.add_argument('--e2e', action='store_true', help='Run end-to-end tests only')
    parser.add_argument('--api', action='store_true', help='Run API tests only')
    parser.add_argument('--content', action='store_true', help='Run content generation tests only')
    parser.add_argument('--session', action='store_true', help='Run session management tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report only')
    parser.add_argument('--check-services', action='store_true', help='Check service health only')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # If no specific test type specified, run all
    if not any([args.unit, args.integration, args.security, args.e2e, args.api, 
                args.content, args.session, args.performance, args.coverage, args.check_services]):
        args.all = True
    
    print("🚀 Course Creator Platform Test Runner")
    print(f"Project root: {runner.project_root}")
    
    # Environment check
    if not runner.check_environment():
        print("❌ Environment check failed. Please install required packages.")
        sys.exit(1)
    
    success = True
    
    # Service health check
    if args.check_services or args.all or args.api or args.e2e:
        print("\n🏥 Checking service health...")
        services_healthy = runner.check_services_health()
        if not services_healthy and (args.api or args.e2e):
            print("⚠️  Some services are not healthy. API and E2E tests may fail.")
    
    # Run selected tests
    if args.unit or args.all:
        success &= runner.run_unit_tests()
    
    if args.content or args.all:
        success &= runner.run_content_generation_tests()
    
    if args.session or args.all:
        success &= runner.run_session_management_tests()
    
    if args.security or args.all:
        success &= runner.run_security_tests()
    
    if args.integration or args.all:
        success &= runner.run_integration_tests()
    
    if args.performance or args.all:
        success &= runner.run_performance_tests()
    
    if args.api:
        success &= runner.run_api_tests()
    
    if args.e2e:
        success &= runner.run_e2e_tests()
    
    if args.coverage or args.all:
        runner.run_coverage_report()
    
    # Print summary
    final_success = runner.print_summary()
    
    if final_success and success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()