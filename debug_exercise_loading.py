#!/usr/bin/env python3
"""Debug exercise loading in lab environment"""

import requests
import time

def test_exercise_loading():
    """Test if exercises are loading properly"""
    course_id = "b892987a-0781-471c-81b6-09e09654adf2"
    
    print("=== Testing Exercise Loading ===")
    
    # Test 1: Check exercises endpoint
    print("\n1. Testing exercises endpoint...")
    response = requests.get(f"http://localhost:8001/exercises/{course_id}")
    
    if response.status_code == 200:
        data = response.json()
        exercises = data.get('exercises', [])
        print(f"✓ Found {len(exercises)} exercises")
        
        if exercises:
            print(f"✓ First exercise: {exercises[0]['title']}")
            print(f"✓ Exercise structure: {list(exercises[0].keys())}")
        else:
            print("✗ No exercises found")
    else:
        print(f"✗ Exercises endpoint failed: {response.status_code}")
    
    # Test 2: Check lab page with direct URL
    print("\n2. Testing lab page access...")
    lab_url = f"http://localhost:8080/lab.html?courseId={course_id}&course=Python%20Programming"
    response = requests.get(lab_url)
    
    if response.status_code == 200:
        print("✓ Lab page accessible")
        
        # Check if JavaScript files are referenced
        content = response.text
        if 'lab-template.js' in content:
            print("✓ lab-template.js referenced")
        else:
            print("✗ lab-template.js not found")
            
        if 'config.js' in content:
            print("✓ config.js referenced")
        else:
            print("✗ config.js not found")
    else:
        print(f"✗ Lab page failed: {response.status_code}")
    
    # Test 3: Check if config.js is accessible
    print("\n3. Testing config.js access...")
    config_response = requests.get("http://localhost:8080/js/config.js")
    
    if config_response.status_code == 200:
        print("✓ config.js accessible")
        config_content = config_response.text
        if 'EXERCISES' in config_content:
            print("✓ EXERCISES endpoint found in config")
        else:
            print("✗ EXERCISES endpoint not found in config")
    else:
        print(f"✗ config.js failed: {config_response.status_code}")
    
    # Test 4: Check if lab-template.js is accessible
    print("\n4. Testing lab-template.js access...")
    js_response = requests.get("http://localhost:8080/js/lab-template.js")
    
    if js_response.status_code == 200:
        print("✓ lab-template.js accessible")
        js_content = js_response.text
        
        functions_to_check = ['loadExercises', 'displayExercises', 'initializeAfterLoad']
        for func in functions_to_check:
            if func in js_content:
                print(f"✓ {func} function found")
            else:
                print(f"✗ {func} function not found")
    else:
        print(f"✗ lab-template.js failed: {js_response.status_code}")

if __name__ == "__main__":
    test_exercise_loading()