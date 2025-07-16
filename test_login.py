#!/usr/bin/env python3
"""
Test login with instructor credentials and check courses API
"""
import requests
import json

def test_login_and_courses():
    """Test login and course loading"""
    
    # Test login
    print("Testing login...")
    login_data = {
        "username": "instructor@courseplatform.com",
        "password": "Instructor123!"
    }
    
    # Try login
    response = requests.post("http://localhost:8000/auth/login", data=login_data)
    print(f"Login response status: {response.status_code}")
    print(f"Login response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"Login successful! Token: {token[:50]}...")
        
        # Test courses API
        print("\nTesting courses API...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        courses_response = requests.get("http://localhost:8004/courses", headers=headers)
        print(f"Courses response status: {courses_response.status_code}")
        print(f"Courses response: {courses_response.text}")
        
        if courses_response.status_code == 200:
            courses_data = courses_response.json()
            print(f"Success! Found {len(courses_data)} courses")
            for course in courses_data:
                print(f"  - {course.get('title', 'Unknown')} ({course.get('id', 'No ID')})")
            
            return token, courses_data
        else:
            print(f"Courses API failed: {courses_response.status_code}")
            return token, None
    else:
        print(f"Login failed: {response.status_code}")
        return None, None

if __name__ == "__main__":
    token, courses = test_login_and_courses()
    
    if token and courses:
        print(f"\n✅ Success! Found {len(courses)} courses with valid token")
        print("Token can be used to test instructor dashboard manually")
    else:
        print("\n❌ Failed to get valid token or courses")