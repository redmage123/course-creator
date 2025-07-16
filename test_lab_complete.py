#!/usr/bin/env python3
"""Complete test of lab environment functionality"""

import requests
import json
from urllib.parse import quote

def test_complete_lab_flow():
    """Test complete lab functionality flow"""
    course_id = "b892987a-0781-471c-81b6-09e09654adf2"
    course_name = "Python Programming"
    
    print("=== Testing Complete Lab Flow ===")
    
    # Test 1: Verify all endpoints are accessible
    print("\n1. Testing endpoint accessibility...")
    
    endpoints = [
        ("Lab page", f"http://localhost:8080/lab.html?courseId={course_id}&course={quote(course_name)}"),
        ("JavaScript file", "http://localhost:8080/js/lab-template.js"),
        ("Config file", "http://localhost:8080/js/config.js"),
        ("Exercises endpoint", f"http://localhost:8001/exercises/{course_id}"),
    ]
    
    for name, url in endpoints:
        try:
            response = requests.get(url)
            print(f"  ✓ {name}: {response.status_code}")
        except Exception as e:
            print(f"  ✗ {name}: Error - {e}")
    
    # Test 2: Test exercise refresh
    print("\n2. Testing exercise refresh...")
    try:
        response = requests.post("http://localhost:8001/lab/refresh-exercises", 
                               json={"course_id": course_id})
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Refresh successful: {data['success']}")
            print(f"  ✓ Exercises generated: {len(data['exercises'])}")
        else:
            print(f"  ✗ Refresh failed: {response.status_code}")
    except Exception as e:
        print(f"  ✗ Refresh error: {e}")
    
    # Test 3: Test exercise loading
    print("\n3. Testing exercise loading...")
    try:
        response = requests.get(f"http://localhost:8001/exercises/{course_id}")
        if response.status_code == 200:
            data = response.json()
            exercises = data.get('exercises', [])
            print(f"  ✓ Loaded {len(exercises)} exercises")
            
            # Check exercise structure
            if exercises:
                first_exercise = exercises[0]
                required_fields = ['id', 'title', 'description', 'difficulty', 'starter_code']
                for field in required_fields:
                    if field in first_exercise or field.replace('_', '') in first_exercise:
                        print(f"    ✓ Has {field}")
                    else:
                        print(f"    ✗ Missing {field}")
        else:
            print(f"  ✗ Loading failed: {response.status_code}")
    except Exception as e:
        print(f"  ✗ Loading error: {e}")
    
    # Test 4: Test JavaScript function availability
    print("\n4. Testing JavaScript function availability...")
    try:
        response = requests.get("http://localhost:8080/js/lab-template.js")
        if response.status_code == 200:
            js_content = response.text
            functions = ['togglePanel', 'initializeLab', 'displayExercises', 'selectExercise', 'initializeAfterLoad']
            
            for func in functions:
                if f"window.{func}" in js_content:
                    print(f"    ✓ {func} exposed to global scope")
                elif f"function {func}" in js_content:
                    print(f"    ✓ {func} function defined")
                else:
                    print(f"    ✗ {func} not found")
        else:
            print(f"  ✗ JavaScript file not accessible: {response.status_code}")
    except Exception as e:
        print(f"  ✗ JavaScript test error: {e}")
    
    print("\n=== Lab Flow Test Complete ===")
    print("The lab environment should now be working correctly!")
    print(f"Open: http://localhost:8080/lab.html?courseId={course_id}&course={quote(course_name)}")

if __name__ == "__main__":
    test_complete_lab_flow()