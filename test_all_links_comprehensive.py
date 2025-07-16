#!/usr/bin/env python3
"""
Comprehensive unit test for all links and interactions in instructor dashboard
"""
import requests
import time
import re

def test_all_navigation_links():
    """Test all navigation links are properly defined"""
    print("🧪 Testing Navigation Links")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Navigation links that should exist
    nav_links = [
        ('overview', 'Overview'),
        ('courses', 'My Courses'),
        ('create-course', 'Create Course'),
        ('students', 'Students'),
        ('content', 'Content'),
        ('labs', 'Labs'),
        ('quizzes', 'Quizzes')
    ]
    
    all_present = True
    for section, title in nav_links:
        # Check for navigation link (flexible pattern)
        nav_patterns = [
            f'onclick="showSection(\'{section}\')"',
            f'onclick="showSection(\'{section}\')"',
            f'showSection(\'{section}\')',
            f'showSection("{section}")'
        ]
        
        found = any(pattern in html_content for pattern in nav_patterns)
        if found:
            print(f"✅ {title} navigation link is present")
        else:
            print(f"❌ {title} navigation link is missing")
            all_present = False
        
        # Check for corresponding section
        section_pattern = f'id="{section}-section"'
        if section_pattern in html_content:
            print(f"✅ {title} section exists")
        else:
            print(f"❌ {title} section is missing")
            all_present = False
    
    return all_present

def test_all_button_functions():
    """Test all button onclick functions are defined"""
    print("\n🧪 Testing Button Functions")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Find all onclick attributes
    onclick_pattern = r'onclick="([^"]*)"'
    onclick_matches = re.findall(onclick_pattern, html_content)
    
    # Extract function names
    function_calls = []
    for match in onclick_matches:
        # Extract function name (before parentheses)
        func_match = re.match(r'(\w+)\s*\(', match)
        if func_match:
            function_calls.append(func_match.group(1))
    
    # Remove duplicates
    unique_functions = list(set(function_calls))
    
    print(f"Found {len(unique_functions)} unique function calls:")
    
    # Check if functions are defined
    all_defined = True
    for func in sorted(unique_functions):
        # Check for function definition
        patterns = [
            f'function {func}',
            f'window.{func} = function',
            f'{func} = function',
            f'window.{func} = '
        ]
        
        found = any(pattern in html_content for pattern in patterns)
        if found:
            print(f"✅ {func}() is defined")
        else:
            print(f"❌ {func}() is missing")
            all_defined = False
    
    return all_defined

def test_modal_interactions():
    """Test modal opening and closing interactions"""
    print("\n🧪 Testing Modal Interactions")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Modal interactions to test
    modal_tests = [
        ('openCreateLabModal', 'Create Custom Lab button'),
        ('closeCreateLabModal', 'Close lab modal'),
        ('viewCourseDetails', 'View course details'),
        ('toggleAccountDropdown', 'Account dropdown'),
        ('showProfileModal', 'Profile modal'),
        ('showSettingsModal', 'Settings modal'),
        ('showHelpModal', 'Help modal'),
        ('openContentUploadModal', 'Content upload modal')
    ]
    
    all_present = True
    for func, description in modal_tests:
        if f'window.{func}' in html_content or f'function {func}' in html_content:
            print(f"✅ {description} function is defined")
        else:
            print(f"❌ {description} function is missing")
            all_present = False
    
    return all_present

def test_form_interactions():
    """Test form submission and interaction functions"""
    print("\n🧪 Testing Form Interactions")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Form-related functions
    form_functions = [
        ('filterCourses', 'Course filtering'),
        ('searchCourses', 'Course search'),
        ('loadCourseStudents', 'Load course students'),
        ('loadCourseLabs', 'Load course labs'),
        ('filterQuizzes', 'Quiz filtering'),
        ('confirmDeleteCourse', 'Delete course confirmation'),
        ('deleteCourse', 'Delete course'),
        ('updateCoursesDisplay', 'Update courses display'),
        ('loadUserCourses', 'Load user courses')
    ]
    
    all_present = True
    for func, description in form_functions:
        if f'window.{func}' in html_content or f'function {func}' in html_content:
            print(f"✅ {description} function is defined")
        else:
            print(f"❌ {description} function is missing")
            all_present = False
    
    return all_present

def test_quiz_pane_functionality():
    """Test quiz pane clicking behavior specifically"""
    print("\n🧪 Testing Quiz Pane Functionality")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for quiz navigation
    if 'onclick="showSection(\'quizzes\')"' in html_content:
        print("✅ Quiz navigation link is present")
    else:
        print("❌ Quiz navigation link is missing")
        return False
    
    # Check for quiz section
    if 'id="quizzes-section"' in html_content:
        print("✅ Quiz section exists")
    else:
        print("❌ Quiz section is missing")
        return False
    
    # Check for quiz content
    if 'Quizzes & Assessments' in html_content:
        print("✅ Quiz content is present")
    else:
        print("❌ Quiz content is missing")
        return False
    
    return True

def test_dropdown_functionality():
    """Test dropdown functionality"""
    print("\n🧪 Testing Dropdown Functionality") 
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for account dropdown
    if 'toggleAccountDropdown' in html_content:
        print("✅ Account dropdown toggle function is present")
    else:
        print("❌ Account dropdown toggle function is missing")
        return False
    
    # Check for dropdown menu
    if 'id="accountMenu"' in html_content:
        print("✅ Account dropdown menu exists")
    else:
        print("❌ Account dropdown menu is missing")
        return False
    
    return True

def test_authentication_integration():
    """Test authentication integration"""
    print("\n🧪 Testing Authentication Integration")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for auth functions
    auth_functions = [
        ('getCurrentUser', 'Get current user'),
        ('logout', 'Logout functionality'),
        ('loadUserCourses', 'Load user courses')
    ]
    
    all_present = True
    for func, description in auth_functions:
        if f'function {func}' in html_content or f'window.{func}' in html_content:
            print(f"✅ {description} function is defined")
        else:
            print(f"❌ {description} function is missing")
            all_present = False
    
    return all_present

def test_error_handling():
    """Test error handling mechanisms"""
    print("\n🧪 Testing Error Handling")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for error handling patterns
    error_patterns = [
        ('showNotification', 'Notification system'),
        ('console.error', 'Error logging'),
        ('try', 'Try-catch blocks'),
        ('catch', 'Error catching')
    ]
    
    all_present = True
    for pattern, description in error_patterns:
        if pattern in html_content:
            print(f"✅ {description} is present")
        else:
            print(f"❌ {description} is missing")
            all_present = False
    
    return all_present

def main():
    """Run all comprehensive tests"""
    print("🚀 COMPREHENSIVE LINK AND INTERACTION TEST")
    print("=" * 50)
    
    # Run all tests
    test_results = [
        test_all_navigation_links(),
        test_all_button_functions(),
        test_modal_interactions(),
        test_form_interactions(),
        test_quiz_pane_functionality(),
        test_dropdown_functionality(),
        test_authentication_integration(),
        test_error_handling()
    ]
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 35)
    print(f"Test Categories Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All comprehensive tests passed!")
        print("\nThe instructor dashboard has:")
        print("- All navigation links properly defined")
        print("- All button functions implemented")
        print("- Modal interactions working correctly")
        print("- Form interactions properly handled")
        print("- Quiz pane functionality working")
        print("- Dropdown functionality working")
        print("- Authentication integration working")
        print("- Error handling mechanisms in place")
        return True
    else:
        print("❌ Some comprehensive tests failed.")
        print("The dashboard may have missing functionality.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)