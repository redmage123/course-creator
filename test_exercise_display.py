#!/usr/bin/env python3
"""Test exercise loading and display functionality"""

import requests
import json

def test_exercise_generation():
    """Test exercise generation for a course"""
    course_id = "b892987a-0781-471c-81b6-09e09654adf2"
    
    try:
        # Test refresh lab exercises endpoint
        print("Testing refresh lab exercises...")
        refresh_response = requests.post(f"http://localhost:8001/refresh-lab-exercises/{course_id}")
        print(f"Refresh status: {refresh_response.status_code}")
        
        if refresh_response.status_code == 200:
            refresh_data = refresh_response.json()
            print(f"✓ Refresh successful: {refresh_data}")
        else:
            print(f"✗ Refresh failed: {refresh_response.text}")
        
        # Test exercise loading
        print("\nTesting exercise loading...")
        exercises_response = requests.get(f"http://localhost:8001/exercises/{course_id}")
        print(f"Exercises status: {exercises_response.status_code}")
        
        if exercises_response.status_code == 200:
            exercises_data = exercises_response.json()
            exercises = exercises_data.get('exercises', [])
            print(f"✓ Found {len(exercises)} exercises")
            
            for i, exercise in enumerate(exercises[:3]):  # Show first 3 exercises
                print(f"  Exercise {i+1}: {exercise.get('title', 'No title')}")
                print(f"    Description: {exercise.get('description', 'No description')[:100]}...")
                print(f"    Difficulty: {exercise.get('difficulty', 'Unknown')}")
                print(f"    Has starter code: {'Yes' if exercise.get('starterCode') or exercise.get('starter_code') else 'No'}")
                print()
        else:
            print(f"✗ Exercise loading failed: {exercises_response.text}")
            
    except Exception as e:
        print(f"Error testing exercises: {e}")

if __name__ == "__main__":
    test_exercise_generation()