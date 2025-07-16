#!/usr/bin/env python3
"""
Simple test to validate the course view fix without browser automation
"""
import requests
import re

def test_authentication_and_api():
    """Test that authentication and API work correctly"""
    
    print("Testing authentication and API functionality...")
    
    # Test bbrelin authentication
    login_data = {
        "username": "bbrelin@gmail.com",
        "password": "f00bar123"
    }
    
    response = requests.post("http://localhost:8000/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return False
    
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
        return False
    
    courses = courses_response.json()
    print(f"✅ API returned {len(courses)} courses for bbrelin")
    
    if len(courses) == 0:
        print("❌ No courses found for bbrelin")
        return False
    
    # Check course structure
    course = courses[0]
    required_fields = ['id', 'title', 'description', 'category', 'difficulty_level', 'estimated_duration']
    
    for field in required_fields:
        if field not in course:
            print(f"❌ Missing required field: {field}")
            return False
    
    print(f"✅ Course has all required fields: {course['title']}")
    return True

def test_html_structure():
    """Test that the HTML contains the necessary elements and functions"""
    
    print("\nTesting HTML structure and JavaScript functions...")
    
    # Read the HTML file
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ Failed to read HTML file: {e}")
        return False
    
    # Check for required functions
    required_functions = [
        'viewCourseDetails',
        'confirmDeleteCourse',
        'deleteCourse',
        'updateCoursesDisplay'
    ]
    
    for func in required_functions:
        if f'function {func}' in html_content:
            print(f"✅ Found function: {func}")
        else:
            print(f"❌ Missing function: {func}")
            return False
    
    # Check for horizontal button styling
    if 'display: flex; gap: 10px' in html_content:
        print("✅ Found horizontal button styling")
    else:
        print("❌ Missing horizontal button styling")
        return False
    
    # Check for modal styles
    if 'modal-content' in html_content and 'modal-header' in html_content:
        print("✅ Found modal styling")
    else:
        print("❌ Missing modal styling")
        return False
    
    # Check for course actions buttons
    button_patterns = [
        r'Edit Content',
        r'viewCourseDetails',
        r'confirmDeleteCourse'
    ]
    
    for pattern in button_patterns:
        if re.search(pattern, html_content):
            print(f"✅ Found button pattern: {pattern}")
        else:
            print(f"❌ Missing button pattern: {pattern}")
            return False
    
    print("✅ HTML structure validation passed")
    return True

def test_course_card_structure():
    """Test that the course card structure is correct"""
    
    print("\nTesting course card structure...")
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ Failed to read HTML file: {e}")
        return False
    
    # Check for enhanced course card structure
    required_elements = [
        'course-card enhanced',
        'course-header',
        'course-body',
        'course-actions',
        'course-status',
        'course-meta'
    ]
    
    for element in required_elements:
        if element in html_content:
            print(f"✅ Found element: {element}")
        else:
            print(f"❌ Missing element: {element}")
            return False
    
    print("✅ Course card structure validation passed")
    return True

def main():
    """Run all tests"""
    
    print("🧪 Testing Course View Fix Implementation\n")
    
    # Test 1: Authentication and API
    test1_passed = test_authentication_and_api()
    
    # Test 2: HTML Structure
    test2_passed = test_html_structure()
    
    # Test 3: Course Card Structure
    test3_passed = test_course_card_structure()
    
    # Overall result
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Authentication works")
        print("✅ API returns course data")
        print("✅ HTML contains required functions")
        print("✅ Buttons are styled horizontally")
        print("✅ Modal functionality is implemented")
        print("✅ Course card structure is correct")
        print("\nThe course view fix should work correctly!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("The course view fix may have issues.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)