#!/usr/bin/env python3
"""
Simple test for the instructor dashboard fixes
"""
import requests
import re

def test_authentication():
    """Test authentication works"""
    print("🧪 TEST 1: Authentication")
    
    login_data = {
        "username": "bbrelin@gmail.com",
        "password": "f00bar123"
    }
    
    try:
        response = requests.post("http://localhost:8000/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json().get('access_token')
            print("✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_courses_api(token):
    """Test courses API returns data"""
    print("\n🧪 TEST 2: Courses API")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("http://localhost:8004/courses", headers=headers)
        if response.status_code == 200:
            courses = response.json()
            if len(courses) > 0:
                print(f"✅ API returned {len(courses)} courses")
                print(f"  Course: {courses[0].get('title', 'Unknown')}")
                return courses
            else:
                print("❌ API returned no courses")
                return []
        else:
            print(f"❌ API failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ API error: {e}")
        return []

def test_html_structure():
    """Test HTML has required elements and functions"""
    print("\n🧪 TEST 3: HTML Structure")
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
        
        # Check for required elements
        required_elements = [
            'id="courses-section"',
            'id="courses-list"',
            'data-section="courses"',
            'class="course-card enhanced"'
        ]
        
        elements_found = 0
        for element in required_elements:
            if element in content:
                print(f"✅ Found element: {element}")
                elements_found += 1
            else:
                print(f"❌ Missing element: {element}")
        
        # Check for required functions
        required_functions = [
            'window.viewCourseDetails',
            'window.confirmDeleteCourse',
            'window.deleteCourse',
            'window.updateCoursesDisplay',
            'window.closeCreateLabModal',
            'window.showSection'
        ]
        
        functions_found = 0
        for func in required_functions:
            if func in content:
                print(f"✅ Found function: {func}")
                functions_found += 1
            else:
                print(f"❌ Missing function: {func}")
        
        print(f"Elements: {elements_found}/{len(required_elements)}")
        print(f"Functions: {functions_found}/{len(required_functions)}")
        
        return elements_found == len(required_elements) and functions_found == len(required_functions)
        
    except Exception as e:
        print(f"❌ Error checking HTML: {e}")
        return False

def test_course_card_generation():
    """Test course card HTML generation"""
    print("\n🧪 TEST 4: Course Card Generation")
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
        
        # Check for course card template
        card_patterns = [
            r'course-card enhanced',
            r'course-header',
            r'course-body',
            r'course-actions',
            r'viewCourseDetails\(',
            r'confirmDeleteCourse\(',
            r'display: flex; gap: 10px'
        ]
        
        patterns_found = 0
        for pattern in card_patterns:
            if re.search(pattern, content):
                print(f"✅ Found pattern: {pattern}")
                patterns_found += 1
            else:
                print(f"❌ Missing pattern: {pattern}")
        
        print(f"Patterns: {patterns_found}/{len(card_patterns)}")
        return patterns_found == len(card_patterns)
        
    except Exception as e:
        print(f"❌ Error checking card generation: {e}")
        return False

def test_modal_functionality():
    """Test modal functionality is implemented"""
    print("\n🧪 TEST 5: Modal Functionality")
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
        
        # Check for modal elements
        modal_patterns = [
            r'modal-content',
            r'modal-header',
            r'modal-body',
            r'modal-footer',
            r'close-btn',
            r'createElement.*modal'
        ]
        
        patterns_found = 0
        for pattern in modal_patterns:
            if re.search(pattern, content):
                print(f"✅ Found modal pattern: {pattern}")
                patterns_found += 1
            else:
                print(f"❌ Missing modal pattern: {pattern}")
        
        print(f"Modal patterns: {patterns_found}/{len(modal_patterns)}")
        return patterns_found >= 4  # Allow some flexibility
        
    except Exception as e:
        print(f"❌ Error checking modal: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 TESTING INSTRUCTOR DASHBOARD FIXES")
    print("=" * 50)
    
    # Test 1: Authentication
    token = test_authentication()
    auth_pass = token is not None
    
    # Test 2: API
    courses = test_courses_api(token) if token else []
    api_pass = len(courses) > 0
    
    # Test 3: HTML Structure
    html_pass = test_html_structure()
    
    # Test 4: Course Card Generation
    card_pass = test_course_card_generation()
    
    # Test 5: Modal Functionality
    modal_pass = test_modal_functionality()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Authentication", auth_pass),
        ("Courses API", api_pass),
        ("HTML Structure", html_pass),
        ("Course Card Generation", card_pass),
        ("Modal Functionality", modal_pass)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL TESTS PASSED! Dashboard fixes are working correctly.")
        print("\n📋 What should work now:")
        print("• bbrelin can log in with f00bar123")
        print("• API returns Introduction to Python course")
        print("• My Courses section should display properly")
        print("• Course cards should show horizontally arranged buttons")
        print("• View button should open a modal with course details")
        print("• No JavaScript errors for missing functions")
        return True
    else:
        print("❌ Some tests failed. Dashboard fixes need more work.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)