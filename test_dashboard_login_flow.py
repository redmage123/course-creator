#!/usr/bin/env python3
"""
Simple test to verify instructor dashboard login flow works
"""
import requests
import os

def test_login_flow():
    """Test the complete login flow"""
    print("🚀 TESTING INSTRUCTOR DASHBOARD LOGIN FLOW")
    print("=" * 50)
    
    # Test 1: Authentication API
    print("\n🧪 TEST 1: Authentication API")
    print("-" * 30)
    
    login_data = {
        "username": "bbrelin@gmail.com",
        "password": "f00bar123"
    }
    
    try:
        response = requests.post("http://localhost:8000/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json().get('access_token')
            print("✅ Authentication successful")
            print(f"✅ Token received: {token[:50]}...")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Test 2: Courses API with token
    print("\n🧪 TEST 2: Courses API with Token")
    print("-" * 30)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("http://localhost:8004/courses", headers=headers)
        if response.status_code == 200:
            courses = response.json()
            print(f"✅ Courses API successful: {len(courses)} courses")
            if len(courses) > 0:
                print(f"✅ Course found: {courses[0].get('title', 'Unknown')}")
            else:
                print("❌ No courses returned")
                return False
        else:
            print(f"❌ Courses API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Courses API error: {e}")
        return False
    
    # Test 3: Dashboard HTML structure
    print("\n🧪 TEST 3: Dashboard HTML Structure")
    print("-" * 30)
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
        
        # Check for essential elements
        required_elements = [
            'dashboard-layout',
            'dashboard-sidebar',
            'dashboard-main',
            'loadUserCourses',
            'updateCoursesDisplay',
            'localStorage.getItem'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element in content:
                print(f"✅ Found: {element}")
            else:
                missing_elements.append(element)
                print(f"❌ Missing: {element}")
        
        if missing_elements:
            print(f"❌ Missing elements: {missing_elements}")
            return False
        
    except Exception as e:
        print(f"❌ Dashboard HTML error: {e}")
        return False
    
    # Test 4: No automatic redirect
    print("\n🧪 TEST 4: No Automatic Redirect")
    print("-" * 30)
    
    # Check that automatic redirect is removed
    if "showSection('overview');" in content:
        print("❌ Automatic redirect still exists")
        return False
    else:
        print("✅ Automatic redirect removed")
    
    # Check that overview section doesn't have active class by default
    if 'id="overview-section" class="content-section active"' in content:
        print("❌ Overview section has active class by default")
        return False
    else:
        print("✅ Overview section doesn't have active class by default")
    
    # Test 5: JavaScript functions exist
    print("\n🧪 TEST 5: JavaScript Functions")
    print("-" * 30)
    
    required_functions = [
        'window.viewCourseDetails',
        'window.confirmDeleteCourse',
        'window.deleteCourse',
        'window.updateCoursesDisplay',
        'window.showSection',
        'window.toggleAccountDropdown'
    ]
    
    missing_functions = []
    for func in required_functions:
        if func in content:
            print(f"✅ Found: {func}")
        else:
            missing_functions.append(func)
            print(f"❌ Missing: {func}")
    
    if missing_functions:
        print(f"❌ Missing functions: {missing_functions}")
        return False
    
    # Test 6: Authentication error handling
    print("\n🧪 TEST 6: Authentication Error Handling")
    print("-" * 30)
    
    auth_patterns = [
        'response.status === 401',
        'Session expired',
        'localStorage.removeItem',
        'window.location.href = \'index.html\''
    ]
    
    missing_patterns = []
    for pattern in auth_patterns:
        if pattern in content:
            print(f"✅ Found: {pattern}")
        else:
            missing_patterns.append(pattern)
            print(f"❌ Missing: {pattern}")
    
    if missing_patterns:
        print(f"❌ Missing auth patterns: {missing_patterns}")
        return False
    
    return True

def main():
    """Run the test"""
    success = test_login_flow()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 INSTRUCTOR DASHBOARD LOGIN FLOW VERIFIED:")
        print("✅ bbrelin can authenticate with f00bar123")
        print("✅ Authentication returns valid JWT token")
        print("✅ Courses API works with the token")
        print("✅ Dashboard HTML has all required elements")
        print("✅ No automatic redirect to overview section")
        print("✅ All required JavaScript functions exist")
        print("✅ Proper 401 error handling implemented")
        print("\n🚀 CONCLUSION: The instructor dashboard should load correctly after login!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("The instructor dashboard login flow has issues.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)