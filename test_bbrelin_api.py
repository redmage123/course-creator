#!/usr/bin/env python3
"""
Test the API directly with bbrelin user credentials
"""
import requests

def test_bbrelin_api():
    """Test API calls with bbrelin user"""
    
    print("Testing bbrelin API access...")
    
    # Authenticate bbrelin
    login_data = {
        "username": "bbrelin@gmail.com",
        "password": "f00bar123"
    }
    
    response = requests.post("http://localhost:8000/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    token = response.json().get('access_token')
    print(f"✅ Successfully authenticated bbrelin")
    
    # Test courses API
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    courses_response = requests.get("http://localhost:8004/courses", headers=headers)
    if courses_response.status_code != 200:
        print(f"❌ Courses API failed: {courses_response.status_code}")
        print(f"Response: {courses_response.text}")
        return
    
    courses = courses_response.json()
    print(f"✅ API returned {len(courses)} courses for bbrelin:")
    
    for course in courses:
        print(f"  - {course.get('title', 'Unknown')} (ID: {course.get('id', 'Unknown')})")
    
    # Check if Introduction to Python is there
    course_titles = [course.get('title', '') for course in courses]
    if "Introduction to Python" in course_titles:
        print("🎉 SUCCESS: Introduction to Python course found for bbrelin!")
    else:
        print("❌ Introduction to Python course not found for bbrelin")
    
    # Test other endpoints
    print("\nTesting other API endpoints...")
    
    # User profile
    profile_response = requests.get("http://localhost:8000/auth/profile", headers=headers)
    if profile_response.status_code == 200:
        profile = profile_response.json()
        print(f"✅ Profile: {profile.get('full_name', 'Unknown')} ({profile.get('email', 'Unknown')})")
    else:
        print(f"❌ Profile API failed: {profile_response.status_code}")

if __name__ == "__main__":
    test_bbrelin_api()