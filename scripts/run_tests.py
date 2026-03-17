#!/usr/bin/env python3
"""
Test automation script for Course Creator Platform.

This script provides a comprehensive test runner that can execute
different types of tests (unit, integration, e2e) with various
configurations and reporting options.
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime
from pathlib import Path
import json
import shutil


class TestRunner:
    """Test runner for Course Creator Platform."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "coverage"
        self.reports_dir = self.project_root / "test_reports"
        self.services_dir = self.project_root / "services"
        self.frontend_dir = self.project_root / "frontend"
        
        # Ensure directories exist
        self.coverage_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Test categories
        self.test_categories = {
            "unit": "tests/unit",
            "integration": "tests/integration",
            "e2e": "tests/e2e",
            "frontend": "tests/frontend",
            "security": "tests/security",
            "performance": "tests/performance"
        }
        
        # Service ports for integration tests
        self.service_ports = {
            "user-management": 8000,
            "course-generator": 8001,
            "content-storage": 8003,
            "course-management": 8004,
            "content-management": 8005
        }
    
    def check_dependencies(self):
        """Check if all required dependencies are installed."""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            "pytest",
            "pytest-cov",
            "pytest-asyncio",
            "pytest-html",
            "pytest-xdist",
            "requests",
            "httpx"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install -r test_requirements.txt")
            return False
        
        print("✅ All dependencies are installed")
        return True
    
    def check_services(self):
        """Check if required services are running."""
        print("🔍 Checking services...")
        
        import requests
        running_services = []
        failed_services = []
        
        for service, port in self.service_ports.items():
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                if response.status_code == 200:
                    running_services.append(service)
                else:
                    failed_services.append(service)
            except requests.exceptions.RequestException:
                failed_services.append(service)
        
        if running_services:
            print(f"✅ Running services: {', '.join(running_services)}")
        
        if failed_services:
            print(f"⚠️  Not running: {', '.join(failed_services)}")
            print("Some integration tests may be skipped")
        
        return len(running_services) > 0
    
    def run_unit_tests(self, coverage=True, verbose=False):
        """Run unit tests."""
        print("🧪 Running unit tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "unit"),
            "-m", "unit",
            "--tb=short"
        ]
        
        if coverage:
            cmd.extend([
                "--cov=services",
                "--cov-report=html:coverage/unit",
                "--cov-report=term-missing",
                "--cov-fail-under=80"
            ])
        
        if verbose:
            cmd.append("-v")
        
        # Add parallel execution
        cmd.extend(["-n", "auto"])
        
        # Add HTML report
        cmd.extend([
            "--html=test_reports/unit_tests.html",
            "--self-contained-html"
        ])
        
        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        # Check services first
        if not self.check_services():
            print("⚠️  Some services are not running. Integration tests may fail.")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "integration"),
            "-m", "integration",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        # Add HTML report
        cmd.extend([
            "--html=test_reports/integration_tests.html",
            "--self-contained-html"
        ])
        
        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0
    
    def run_frontend_tests(self, verbose=False):
        """Run frontend tests."""
        print("🎨 Running frontend tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "frontend"),
            "-m", "frontend",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        # Add HTML report
        cmd.extend([
            "--html=test_reports/frontend_tests.html",
            "--self-contained-html"
        ])
        
        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0
    
    def run_security_tests(self, verbose=False):
        """Run security tests."""
        print("🔒 Running security tests...")
        
        # Run bandit security scan
        print("Running bandit security scan...")
        bandit_cmd = [
            "bandit", "-r", "services/", 
            "-f", "json", 
            "-o", "test_reports/security_bandit.json"
        ]
        
        subprocess.run(bandit_cmd, cwd=self.project_root)
        
        # Run safety check
        print("Running safety dependency check...")
        safety_cmd = [
            "safety", "check", 
            "--json", 
            "--output", "test_reports/security_safety.json"
        ]
        
        subprocess.run(safety_cmd, cwd=self.project_root)
        
        # Run pytest security tests
        if (self.test_dir / "security").exists():
            cmd = [
                "python", "-m", "pytest",
                str(self.test_dir / "security"),
                "-m", "security",
                "--tb=short"
            ]
            
            if verbose:
                cmd.append("-v")
            
            cmd.extend([
                "--html=test_reports/security_tests.html",
                "--self-contained-html"
            ])
            
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode == 0
        
        return True
    
    def run_performance_tests(self, verbose=False):
        """Run performance tests."""
        print("⚡ Running performance tests...")
        
        if (self.test_dir / "performance").exists():
            cmd = [
                "python", "-m", "pytest",
                str(self.test_dir / "performance"),
                "-m", "performance",
                "--tb=short",
                "--benchmark-only"
            ]
            
            if verbose:
                cmd.append("-v")
            
            cmd.extend([
                "--html=test_reports/performance_tests.html",
                "--self-contained-html"
            ])
            
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode == 0
        
        return True
    
    def run_e2e_tests(self, verbose=False):
        """Run end-to-end tests."""
        print("🎭 Running end-to-end tests...")
        
        if (self.test_dir / "e2e").exists():
            cmd = [
                "python", "-m", "pytest",
                str(self.test_dir / "e2e"),
                "-m", "e2e",
                "--tb=short"
            ]
            
            if verbose:
                cmd.append("-v")
            
            cmd.extend([
                "--html=test_reports/e2e_tests.html",
                "--self-contained-html"
            ])
            
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode == 0
        
        return True
    
    def run_linting(self):
        """Run code linting."""
        print("🔍 Running code linting...")
        
        # Python linting
        services = [d for d in self.services_dir.iterdir() if d.is_dir()]
        
        for service in services:
            print(f"Linting {service.name}...")
            
            # Run flake8
            flake8_cmd = [
                "flake8", str(service),
                "--output-file", f"test_reports/lint_{service.name}_flake8.txt"
            ]
            subprocess.run(flake8_cmd, cwd=self.project_root)
            
            # Run black check
            black_cmd = [
                "black", "--check", str(service),
                "--diff"
            ]
            subprocess.run(black_cmd, cwd=self.project_root)
            
            # Run isort check
            isort_cmd = [
                "isort", "--check-only", str(service),
                "--diff"
            ]
            subprocess.run(isort_cmd, cwd=self.project_root)
        
        # JavaScript linting (if npm is available)
        if shutil.which("npm"):
            print("Linting JavaScript...")
            npm_cmd = ["npm", "run", "lint"]
            subprocess.run(npm_cmd, cwd=self.frontend_dir)
    
    def run_type_checking(self):
        """Run type checking."""
        print("🔍 Running type checking...")
        
        services = [d for d in self.services_dir.iterdir() if d.is_dir()]
        
        for service in services:
            print(f"Type checking {service.name}...")
            
            mypy_cmd = [
                "mypy", str(service),
                "--html-report", f"test_reports/mypy_{service.name}",
                "--ignore-missing-imports"
            ]
            subprocess.run(mypy_cmd, cwd=self.project_root)
    
    def generate_combined_report(self):
        """Generate combined test report."""
        print("📊 Generating combined test report...")
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_results": {},
            "coverage": {},
            "security": {},
            "performance": {}
        }
        
        # Collect test results
        for category in self.test_categories:
            report_file = self.reports_dir / f"{category}_tests.html"
            if report_file.exists():
                report_data["test_results"][category] = str(report_file)
        
        # Collect coverage data
        coverage_file = self.coverage_dir / "unit" / "index.html"
        if coverage_file.exists():
            report_data["coverage"]["unit"] = str(coverage_file)
        
        # Save report data
        with open(self.reports_dir / "test_summary.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📋 Test reports available in: {self.reports_dir}")
    
    def clean_reports(self):
        """Clean previous test reports."""
        print("🧹 Cleaning previous test reports...")
        
        if self.reports_dir.exists():
            shutil.rmtree(self.reports_dir)
        if self.coverage_dir.exists():
            shutil.rmtree(self.coverage_dir)
        
        self.reports_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
    
    def run_all_tests(self, coverage=True, verbose=False):
        """Run all tests in sequence."""
        print("🚀 Running all tests...")
        start_time = time.time()
        
        results = {}
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Run tests in order
        results["unit"] = self.run_unit_tests(coverage=coverage, verbose=verbose)
        results["integration"] = self.run_integration_tests(verbose=verbose)
        results["frontend"] = self.run_frontend_tests(verbose=verbose)
        results["security"] = self.run_security_tests(verbose=verbose)
        results["performance"] = self.run_performance_tests(verbose=verbose)
        results["e2e"] = self.run_e2e_tests(verbose=verbose)
        
        # Run linting and type checking
        self.run_linting()
        self.run_type_checking()
        
        # Generate combined report
        self.generate_combined_report()
        
        # Print summary
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY ({duration:.2f}s)")
        print(f"{'='*60}")
        
        for category, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{category.upper():<12} {status}")
        
        total_passed = sum(results.values())
        total_tests = len(results)
        
        print(f"\nOverall: {total_passed}/{total_tests} test suites passed")
        
        if total_passed == total_tests:
            print("🎉 All tests passed!")
            return True
        else:
            print("💥 Some tests failed!")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test runner for Course Creator Platform")
    parser.add_argument("--category", choices=["unit", "integration", "frontend", "security", "performance", "e2e", "all"], 
                       default="all", help="Test category to run")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--clean", action="store_true", help="Clean previous reports")
    parser.add_argument("--check-deps", action="store_true", help="Only check dependencies")
    parser.add_argument("--check-services", action="store_true", help="Only check services")
    parser.add_argument("--lint-only", action="store_true", help="Run only linting")
    parser.add_argument("--type-check-only", action="store_true", help="Run only type checking")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Clean reports if requested
    if args.clean:
        runner.clean_reports()
        return
    
    # Check dependencies only
    if args.check_deps:
        return runner.check_dependencies()
    
    # Check services only
    if args.check_services:
        return runner.check_services()
    
    # Run linting only
    if args.lint_only:
        runner.run_linting()
        return
    
    # Run type checking only
    if args.type_check_only:
        runner.run_type_checking()
        return
    
    # Run specific test category
    success = True
    coverage = not args.no_coverage
    
    if args.category == "unit":
        success = runner.run_unit_tests(coverage=coverage, verbose=args.verbose)
    elif args.category == "integration":
        success = runner.run_integration_tests(verbose=args.verbose)
    elif args.category == "frontend":
        success = runner.run_frontend_tests(verbose=args.verbose)
    elif args.category == "security":
        success = runner.run_security_tests(verbose=args.verbose)
    elif args.category == "performance":
        success = runner.run_performance_tests(verbose=args.verbose)
    elif args.category == "e2e":
        success = runner.run_e2e_tests(verbose=args.verbose)
    elif args.category == "all":
        success = runner.run_all_tests(coverage=coverage, verbose=args.verbose)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()