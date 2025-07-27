#!/usr/bin/env python3
"""
Comprehensive Test Runner
Runs all test types in the correct order to catch configuration bugs
"""

import sys
import subprocess
import time
import os
from pathlib import Path
from typing import List, Dict, Tuple

PROJECT_ROOT = Path(__file__).parent

def run_command(command: List[str], description: str, cwd: Path = PROJECT_ROOT) -> Tuple[bool, str]:
    """Run a command and return success status and output"""
    print(f"\n🧪 {description}...")
    print(f"Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} passed")
            return True, result.stdout
        else:
            print(f"❌ {description} failed")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False, "Command timed out"
    except Exception as e:
        print(f"💥 {description} crashed: {e}")
        return False, str(e)

def main():
    """Run comprehensive test suite"""
    print("🚀 Course Creator Comprehensive Test Suite")
    print("This test suite catches configuration bugs that mocks would hide.\n")
    
    # Test execution plan
    test_plan = [
        {
            "name": "Configuration Validation Tests",
            "command": ["python", "-m", "pytest", "tests/config/", "-v", "--tb=short"],
            "description": "Validate service configurations match deployment",
            "critical": True
        },
        {
            "name": "Service Startup Smoke Tests", 
            "command": ["python", "-m", "pytest", "tests/smoke/", "-v", "--tb=short"],
            "description": "Test that all services can actually start",
            "critical": True
        },
        {
            "name": "Real Database Integration Tests",
            "command": ["python", "-m", "pytest", "tests/integration/", "-m", "real_db", "-v", "--tb=short"],
            "description": "Test with real database connections (no mocks)",
            "critical": True,
            "setup": lambda: setup_test_environment(),
            "cleanup": lambda: cleanup_test_environment()
        },
        {
            "name": "Unit Tests",
            "command": ["python", "-m", "pytest", "tests/unit/", "-v", "--cov=services", "--cov-fail-under=80"],
            "description": "Run unit tests with coverage requirements",
            "critical": True
        },
        {
            "name": "Legacy Integration Tests",
            "command": ["python", "-m", "pytest", "tests/integration/", 
                       "--ignore=tests/integration/test_analytics_real_integration.py", "-v"],
            "description": "Run existing integration tests (with mocks)",
            "critical": False
        },
        {
            "name": "Frontend Tests",
            "command": ["python", "-m", "pytest", "tests/frontend/", "-v"],
            "description": "Test frontend functionality", 
            "critical": False
        },
        {
            "name": "End-to-End Tests",
            "command": ["python", "-m", "pytest", "tests/e2e/", "-v", "--tb=short"],
            "description": "Full workflow testing",
            "critical": False
        }
    ]
    
    # Track results
    results = {}
    critical_failures = []
    
    for test_group in test_plan:
        name = test_group["name"]
        command = test_group["command"]
        description = test_group["description"]
        critical = test_group.get("critical", False)
        
        # Run setup if provided
        if "setup" in test_group:
            print(f"\n🔧 Setting up for {name}...")
            try:
                test_group["setup"]()
            except Exception as e:
                print(f"❌ Setup failed for {name}: {e}")
                if critical:
                    critical_failures.append(f"{name} (setup failed)")
                continue
        
        # Run the test
        success, output = run_command(command, f"Running {name}")
        results[name] = {
            "success": success,
            "output": output,
            "critical": critical
        }
        
        # Track critical failures
        if not success and critical:
            critical_failures.append(name)
        
        # Run cleanup if provided
        if "cleanup" in test_group:
            try:
                test_group["cleanup"]()
            except Exception as e:
                print(f"⚠️ Cleanup warning for {name}: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    total_tests = len(test_plan)
    passed_tests = sum(1 for r in results.values() if r["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"Total test groups: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    # Show detailed results
    for name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        critical_marker = " [CRITICAL]" if result["critical"] else ""
        print(f"{status} {name}{critical_marker}")
    
    # Critical failure analysis
    if critical_failures:
        print(f"\n🚨 CRITICAL FAILURES ({len(critical_failures)}):")
        for failure in critical_failures:
            print(f"   - {failure}")
        print("\n❌ BUILD FAILED due to critical test failures")
        print("These tests catch configuration bugs that would cause runtime failures.")
        return 1
    
    if failed_tests > 0:
        print(f"\n⚠️ BUILD UNSTABLE - {failed_tests} non-critical test groups failed")
        return 2
    
    print("\n✅ ALL TESTS PASSED!")
    print("Configuration is consistent and services can start properly.")
    return 0

def setup_test_environment():
    """Setup test environment for real integration tests"""
    setup_script = PROJECT_ROOT / "tests" / "setup_test_environment.py"
    result = subprocess.run([sys.executable, str(setup_script)], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Test environment setup failed: {result.stderr}")

def cleanup_test_environment():  
    """Cleanup test environment"""
    setup_script = PROJECT_ROOT / "tests" / "setup_test_environment.py"
    subprocess.run([sys.executable, str(setup_script), "--cleanup"], capture_output=True)

def install_test_dependencies():
    """Install test dependencies"""
    print("📦 Installing test dependencies...")
    result = subprocess.run([
        sys.executable, "-m", "pip", "install", "-r", "test_requirements.txt"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to install test dependencies: {result.stderr}")
        return False
    
    print("✅ Test dependencies installed")
    return True

if __name__ == "__main__":
    # Check for --install-deps flag
    if "--install-deps" in sys.argv:
        if not install_test_dependencies():
            sys.exit(1)
        sys.argv.remove("--install-deps")
    
    # Check if test dependencies are available
    try:
        import pytest
        import asyncpg
        import psycopg2
        import docker
        import redis
        import yaml
    except ImportError as e:
        print(f"❌ Missing test dependencies: {e}")
        print("Run with --install-deps to install them:")
        print(f"python {sys.argv[0]} --install-deps")
        sys.exit(1)
    
    sys.exit(main())