#!/usr/bin/env python3
"""
Test Environment Setup Script
Sets up proper test environment to catch configuration bugs
"""

import os
import sys
import subprocess
import time
import yaml
import json
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).parent.parent

def setup_test_database():
    """Setup test database environment"""
    print("🗄️  Setting up test database...")
    
    # Start test database
    compose_file = PROJECT_ROOT / "docker-compose.test.yml"
    
    result = subprocess.run([
        'docker-compose', '-f', str(compose_file), 
        'up', '-d', 'postgres-test', 'redis-test'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to start test database: {result.stderr}")
        return False
    
    # Wait for database to be ready
    print("⏳ Waiting for test database to be ready...")
    time.sleep(10)
    
    # Verify database is accessible
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='course_creator_test',
            user='postgres',
            password='test_password'
        )
        conn.close()
        print("✅ Test database is ready")
        return True
    except Exception as e:
        print(f"❌ Test database not accessible: {e}")
        return False

def create_test_user():
    """Create test database user"""
    print("👤 Creating test database user...")
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='course_creator_test',
            user='postgres',
            password='test_password'
        )
        
        cursor = conn.cursor()
        
        # Create test user
        try:
            cursor.execute("""
                CREATE USER course_user WITH PASSWORD 'test_password'
            """)
            cursor.execute("""
                GRANT ALL PRIVILEGES ON DATABASE course_creator_test TO course_user
            """)
            cursor.execute("""
                GRANT ALL PRIVILEGES ON SCHEMA public TO course_user
            """)
            cursor.execute("""
                GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO course_user
            """)
            cursor.execute("""
                GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO course_user
            """)
            conn.commit()
            print("✅ Test user created successfully")
        except psycopg2.errors.DuplicateObject:
            print("ℹ️  Test user already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return False

def setup_test_environment_variables():
    """Setup test environment variables"""
    print("🔧 Setting up test environment variables...")
    
    test_env = {
        'DB_HOST': 'localhost',
        'DB_PORT': '5434',
        'DB_USER': 'course_user',
        'DB_PASSWORD': 'test_password',
        'DB_NAME': 'course_creator_test',
        'REDIS_URL': 'redis://localhost:6380',
        'JWT_SECRET_KEY': 'test-jwt-secret-key-for-testing-only',
        'ANTHROPIC_API_KEY': 'test-api-key',
        'ENVIRONMENT': 'test'
    }
    
    # Write test environment file
    test_env_file = PROJECT_ROOT / '.env.test'
    with open(test_env_file, 'w') as f:
        for key, value in test_env.items():
            f.write(f"{key}={value}\n")
    
    print("✅ Test environment variables configured")
    return True

def verify_test_configuration():
    """Verify test configuration is correct"""
    print("🔍 Verifying test configuration...")
    
    issues = []
    
    # Check docker-compose.test.yml exists
    test_compose = PROJECT_ROOT / "docker-compose.test.yml"
    if not test_compose.exists():
        issues.append("docker-compose.test.yml missing")
    
    # Check test directories exist
    test_dirs = ['tests/config', 'tests/integration', 'tests/smoke']
    for test_dir in test_dirs:
        test_path = PROJECT_ROOT / test_dir
        if not test_path.exists():
            issues.append(f"Test directory {test_dir} missing")
    
    # Check critical test files exist
    critical_tests = [
        'tests/config/test_configuration_validation.py',
        'tests/integration/test_analytics_real_integration.py',
        'tests/smoke/test_service_startup.py'
    ]
    
    for test_file in critical_tests:
        test_path = PROJECT_ROOT / test_file
        if not test_path.exists():
            issues.append(f"Critical test file {test_file} missing")
    
    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ Test configuration verified")
    return True

def install_test_dependencies():
    """Install additional test dependencies"""
    print("📦 Installing test dependencies...")
    
    test_requirements = [
        'psycopg2-binary',
        'docker',
        'redis',
        'pyyaml'
    ]
    
    for requirement in test_requirements:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', requirement
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to install {requirement}: {result.stderr}")
            return False
    
    print("✅ Test dependencies installed")
    return True

def run_configuration_tests():
    """Run configuration validation tests"""
    print("🧪 Running configuration validation tests...")
    
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'tests/config/test_configuration_validation.py',
        '-v'
    ], cwd=PROJECT_ROOT)
    
    return result.returncode == 0

def cleanup_test_environment():
    """Cleanup test environment"""
    print("🧹 Cleaning up test environment...")
    
    compose_file = PROJECT_ROOT / "docker-compose.test.yml"
    subprocess.run([
        'docker-compose', '-f', str(compose_file), 'down', '-v'
    ], capture_output=True)
    
    # Remove test environment file
    test_env_file = PROJECT_ROOT / '.env.test'
    if test_env_file.exists():
        test_env_file.unlink()
    
    print("✅ Test environment cleaned up")

def main():
    """Main setup function"""
    print("🚀 Setting up Course Creator test environment...")
    print("This will catch configuration bugs that mocks would hide.\n")
    
    steps = [
        ("Install test dependencies", install_test_dependencies),
        ("Verify test configuration", verify_test_configuration),
        ("Setup test database", setup_test_database),
        ("Create test user", create_test_user),
        ("Setup environment variables", setup_test_environment_variables),
        ("Run configuration tests", run_configuration_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    print("\n" + "="*60)
    
    if failed_steps:
        print("❌ Test environment setup failed!")
        print("Failed steps:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease fix the issues and run again.")
        return 1
    else:
        print("✅ Test environment setup completed successfully!")
        print("\nYou can now run:")
        print("   pytest tests/config/                    # Configuration tests")
        print("   pytest tests/integration/ -m real_db    # Real database tests")
        print("   pytest tests/smoke/                     # Service startup tests")
        print("\nTo cleanup: python tests/setup_test_environment.py --cleanup")
        return 0

if __name__ == "__main__":
    if "--cleanup" in sys.argv:
        cleanup_test_environment()
    else:
        sys.exit(main())