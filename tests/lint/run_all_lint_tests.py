#!/usr/bin/env python3
"""
COMPREHENSIVE LINT TEST RUNNER
PURPOSE: Execute all linting tests for demo service, frontend JS, and CSS
WHY: Centralized linting ensures consistent code quality across the platform
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def install_python_linting_tools():
    """Install required Python linting tools"""
    tools = [
        "flake8",
        "pycodestyle", 
        "pylint",
        "isort",
        "bandit",
        "mypy",
        "pydocstyle",
        "radon"
    ]
    
    print("Installing Python linting tools...")
    for tool in tools:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", tool], 
                          check=True, capture_output=True)
            print(f"✅ {tool} installed")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {tool}")

def install_node_linting_tools():
    """Install required Node.js linting tools"""
    print("Checking Node.js linting tools...")
    
    # Check if npm is available
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        
        # Install ESLint globally if not present
        try:
            subprocess.run(["npx", "eslint", "--version"], check=True, capture_output=True)
            print("✅ ESLint available")
        except subprocess.CalledProcessError:
            print("Installing ESLint...")
            subprocess.run(["npm", "install", "-g", "eslint"], check=True)
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ npm not available, skipping JavaScript linting tools")

def run_python_lint_tests():
    """Run Python demo service linting tests"""
    print("\n" + "="*60)
    print("RUNNING PYTHON DEMO SERVICE LINT TESTS")
    print("="*60)
    
    lint_test_file = Path(__file__).parent / "test_demo_service_lint.py"
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        str(lint_test_file),
        "-v",
        "--tb=short",
        "--color=yes"
    ], capture_output=False)
    
    return result.returncode == 0

def run_javascript_lint_tests():
    """Run frontend JavaScript linting tests"""
    print("\n" + "="*60)
    print("RUNNING FRONTEND JAVASCRIPT LINT TESTS")
    print("="*60)
    
    lint_test_file = Path(__file__).parent / "test_frontend_javascript_lint.py"
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        str(lint_test_file),
        "-v",
        "--tb=short",
        "--color=yes"
    ], capture_output=False)
    
    return result.returncode == 0

def run_css_lint_tests():
    """Run CSS linting tests"""
    print("\n" + "="*60)
    print("RUNNING CSS LINT TESTS")
    print("="*60)
    
    lint_test_file = Path(__file__).parent / "test_css_lint.py"
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        str(lint_test_file), 
        "-v",
        "--tb=short",
        "--color=yes"
    ], capture_output=False)
    
    return result.returncode == 0

def generate_lint_report():
    """Generate comprehensive lint report"""
    print("\n" + "="*60)
    print("GENERATING COMPREHENSIVE LINT REPORT")
    print("="*60)
    
    report_file = PROJECT_ROOT / "lint_report.txt"
    
    with open(report_file, 'w') as f:
        f.write("Course Creator Platform - Lint Report\n")
        f.write("=" * 40 + "\n\n")
        
        # Demo service stats
        demo_service_path = PROJECT_ROOT / "services" / "demo-service"
        if demo_service_path.exists():
            python_files = list(demo_service_path.glob("*.py"))
            f.write(f"Demo Service Python Files: {len(python_files)}\n")
        
        # Frontend stats  
        frontend_js_path = PROJECT_ROOT / "frontend" / "js"
        if frontend_js_path.exists():
            js_files = list(frontend_js_path.rglob("*.js"))
            f.write(f"Frontend JavaScript Files: {len(js_files)}\n")
        
        # CSS stats
        css_path = PROJECT_ROOT / "frontend" / "css"
        if css_path.exists():
            css_files = list(css_path.rglob("*.css"))
            f.write(f"CSS Files: {len(css_files)}\n")
        
        f.write(f"\nReport generated at: {report_file}\n")
    
    print(f"📄 Lint report saved to: {report_file}")

def main():
    parser = argparse.ArgumentParser(description="Run comprehensive lint tests")
    parser.add_argument("--install-tools", action="store_true", 
                       help="Install required linting tools")
    parser.add_argument("--python-only", action="store_true",
                       help="Run only Python lint tests")
    parser.add_argument("--js-only", action="store_true", 
                       help="Run only JavaScript lint tests")
    parser.add_argument("--css-only", action="store_true",
                       help="Run only CSS lint tests")
    parser.add_argument("--generate-report", action="store_true",
                       help="Generate lint report")
    
    args = parser.parse_args()
    
    if args.install_tools:
        install_python_linting_tools()
        install_node_linting_tools()
        return
    
    print("🔍 Course Creator Platform - Comprehensive Lint Test Suite")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # Run specific tests based on arguments
    if args.python_only:
        total_tests = 1
        if run_python_lint_tests():
            success_count += 1
    elif args.js_only:
        total_tests = 1
        if run_javascript_lint_tests():
            success_count += 1
    elif args.css_only:
        total_tests = 1
        if run_css_lint_tests():
            success_count += 1
    else:
        # Run all tests
        total_tests = 3
        
        if run_python_lint_tests():
            success_count += 1
            
        if run_javascript_lint_tests():
            success_count += 1
            
        if run_css_lint_tests():
            success_count += 1
    
    # Generate report if requested
    if args.generate_report:
        generate_lint_report()
    
    # Summary
    print("\n" + "="*60)
    print("LINT TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {success_count}/{total_tests} test suites")
    
    if success_count == total_tests:
        print("🎉 All lint tests passed! Code quality looks good.")
        sys.exit(0)
    else:
        print("❌ Some lint tests failed. Please review the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()