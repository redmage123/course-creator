#!/usr/bin/env python3
"""
Quick test validation script to verify our fixes.
"""
import sys
import os
from pathlib import Path

def test_import_fixes():
    """Test that our import fixes work"""
    print("Testing import fixes...")
    
    # Add project paths
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Test 1: Exercise generation service import
    try:
        sys.path.insert(0, str(project_root / "services" / "course-generator"))
        from application.services.exercise_generation_service import ExerciseGenerationService
        print("✅ Exercise generation service import: SUCCESS")
    except ImportError as e:
        print(f"❌ Exercise generation service import: FAILED - {e}")
    
    # Test 2: Quiz generation service import
    try:
        from application.services.quiz_generation_service import QuizGenerationService
        print("✅ Quiz generation service import: SUCCESS")
    except ImportError as e:
        print(f"❌ Quiz generation service import: FAILED - {e}")
    
    # Test 3: Analytics service import
    try:
        sys.path.insert(0, str(project_root / "services" / "analytics"))
        from application.services.learning_analytics_service import LearningAnalyticsService
        print("✅ Analytics service import: SUCCESS")
    except ImportError as e:
        print(f"❌ Analytics service import: FAILED - {e}")
    
    # Test 4: Content management imports
    try:
        sys.path.insert(0, str(project_root / "services" / "content-management"))
        from models.content import SyllabusContent
        print("✅ Content management models import: SUCCESS")
    except ImportError as e:
        print(f"❌ Content management models import: FAILED - {e}")

def test_docker_compose_warnings():
    """Test Docker Compose configuration"""
    print("\nTesting Docker Compose configuration...")
    
    compose_file = Path(__file__).parent / "docker-compose.yml"
    override_file = Path(__file__).parent / "docker-compose.override.yml"
    
    # Check version attribute removal
    if compose_file.exists():
        content = compose_file.read_text()
        if "version:" not in content:
            print("✅ Docker Compose version attribute removed: SUCCESS")
        else:
            print("❌ Docker Compose version attribute still present: FAILED")
    
    if override_file.exists():
        content = override_file.read_text()
        if "version:" not in content:
            print("✅ Docker Compose override version attribute removed: SUCCESS")
        else:
            print("❌ Docker Compose override version attribute still present: FAILED")
    
    # Check SMTP environment variable defaults
    if compose_file.exists():
        content = compose_file.read_text()
        if "SMTP_USER=${SMTP_USER:-}" in content:
            print("✅ SMTP environment variables have defaults: SUCCESS")
        else:
            print("❌ SMTP environment variables missing defaults: FAILED")

def check_file_structures():
    """Check critical file structures"""
    print("\nChecking critical file structures...")
    
    project_root = Path(__file__).parent
    
    # Check service directories
    services = [
        "user-management",
        "course-generator", 
        "content-management",
        "course-management",
        "analytics",
        "organization-management"
    ]
    
    for service in services:
        service_path = project_root / "services" / service
        if service_path.exists():
            print(f"✅ Service directory {service}: EXISTS")
        else:
            print(f"❌ Service directory {service}: MISSING")
    
    # Check test directories
    test_dirs = [
        "tests/unit",
        "tests/integration", 
        "tests/frontend",
        "tests/e2e",
        "tests/runners"
    ]
    
    for test_dir in test_dirs:
        test_path = project_root / test_dir
        if test_path.exists():
            print(f"✅ Test directory {test_dir}: EXISTS")
        else:
            print(f"❌ Test directory {test_dir}: MISSING")

if __name__ == "__main__":
    print("🧪 QUICK TEST VALIDATION SCRIPT")
    print("="*50)
    
    test_import_fixes()
    test_docker_compose_warnings()
    check_file_structures()
    
    print("\n" + "="*50)
    print("✅ Validation complete!")