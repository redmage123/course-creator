#!/usr/bin/env python3
"""Test the lab functionality to verify toggle functions work"""

import requests
import subprocess
import time

def test_lab_access():
    """Test that lab page loads and JavaScript functions are available"""
    try:
        # Test lab page access
        response = requests.get("http://localhost:8080/lab.html?courseId=b892987a-0781-471c-81b6-09e09654adf2&course=Test%20Course")
        print(f"Lab page status: {response.status_code}")
        
        # Check if essential files are accessible
        js_response = requests.get("http://localhost:8080/js/lab-template.js")
        print(f"JavaScript file status: {js_response.status_code}")
        
        config_response = requests.get("http://localhost:8080/js/config.js")
        print(f"Config file status: {config_response.status_code}")
        
        # Check if functions are defined in the JS file
        js_content = js_response.text
        functions_to_check = ['togglePanel', 'initializeLab', 'displayExercises', 'selectExercise']
        
        for func in functions_to_check:
            if f"function {func}" in js_content or f"window.{func}" in js_content:
                print(f"✓ {func} function found in JavaScript")
            else:
                print(f"✗ {func} function NOT found in JavaScript")
        
        # Test if exercises endpoint works
        try:
            exercises_response = requests.get("http://localhost:8001/exercises/b892987a-0781-471c-81b6-09e09654adf2")
            print(f"Exercises endpoint status: {exercises_response.status_code}")
            if exercises_response.status_code == 200:
                print("✓ Exercises endpoint working")
            else:
                print(f"✗ Exercises endpoint error: {exercises_response.text}")
        except Exception as e:
            print(f"✗ Exercises endpoint error: {e}")
            
        return True
        
    except Exception as e:
        print(f"Error testing lab access: {e}")
        return False

if __name__ == "__main__":
    print("Testing lab functionality...")
    test_lab_access()