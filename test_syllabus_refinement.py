#!/usr/bin/env python3
"""
Test script to verify syllabus refinement functionality
"""

import json
import requests
import sys

# Test configuration
API_BASE = "http://176.9.99.103:8001"
COURSE_ID = "test_course_123"

# Sample syllabus for testing
SAMPLE_SYLLABUS = {
    "course_title": "Introduction to Python Programming",
    "course_description": "Learn the fundamentals of Python programming",
    "duration": "8 weeks",
    "modules": [
        {
            "module_number": 1,
            "title": "Getting Started with Python",
            "description": "Introduction to Python basics",
            "topics": ["Python installation", "Basic syntax", "Running Python code"],
            "duration": "1 week"
        },
        {
            "module_number": 2,
            "title": "Control Structures",
            "description": "Learning if statements, loops, and functions",
            "topics": ["If statements", "For loops", "While loops", "Functions"],
            "duration": "2 weeks"
        }
    ],
    "learning_objectives": [
        "Understand Python syntax",
        "Write basic Python programs",
        "Use control structures effectively"
    ],
    "prerequisites": ["Basic computer skills"],
    "resources": ["Python.org documentation", "Course materials"]
}

def test_syllabus_refinement():
    """Test syllabus refinement with request to add new module"""
    
    print("🧪 Testing Syllabus Refinement Functionality")
    print("=" * 50)
    
    # Prepare refinement payload
    refinement_payload = {
        "course_id": COURSE_ID,
        "feedback": "Add a new module after module 1 about Python variables and data types. This should cover variables, strings, numbers, lists, and dictionaries.",
        "current_syllabus": SAMPLE_SYLLABUS
    }
    
    print(f"📤 Sending refinement request:")
    print(f"   Course ID: {COURSE_ID}")
    print(f"   Feedback: {refinement_payload['feedback']}")
    print(f"   Original modules: {len(SAMPLE_SYLLABUS['modules'])}")
    
    try:
        # Make API request
        response = requests.post(
            f"{API_BASE}/syllabus/refine",
            json=refinement_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            refined_syllabus = result.get('syllabus', {})
            
            print(f"✅ Refinement successful!")
            print(f"   New modules count: {len(refined_syllabus.get('modules', []))}")
            
            # Check if new module was added
            modules = refined_syllabus.get('modules', [])
            if len(modules) > len(SAMPLE_SYLLABUS['modules']):
                print(f"✅ New module added successfully!")
                
                # Find the new module
                for i, module in enumerate(modules):
                    print(f"   Module {i+1}: {module.get('title', 'N/A')}")
                    if 'variable' in module.get('title', '').lower() or 'data type' in module.get('title', '').lower():
                        print(f"   🎯 Found variables/data types module: {module.get('title')}")
                        print(f"      Topics: {module.get('topics', [])}")
                        
            else:
                print(f"❌ No new module was added (same count: {len(modules)})")
                return False
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def test_health_check():
    """Test if the course generator service is running"""
    
    print("🏥 Testing Service Health")
    print("=" * 30)
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Course generator service is healthy")
            return True
        else:
            print(f"❌ Service health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Service health check error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Course Creator - Syllabus Refinement Test")
    print("=" * 60)
    
    # Test service health first
    if not test_health_check():
        print("\n❌ Service is not healthy, aborting tests")
        sys.exit(1)
    
    print()
    
    # Test syllabus refinement
    if test_syllabus_refinement():
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)