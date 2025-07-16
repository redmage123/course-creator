#!/usr/bin/env python3
"""
Unit test specifically for view button functionality
"""
import requests
import time
import json

def test_view_button_functionality():
    """Test that view button shows course content, not just basic modal"""
    print("🧪 Testing View Button Functionality")
    print("=" * 40)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Test 1: Check if viewCourseDetails function exists
    if 'function viewCourseDetails' in html_content:
        print("✅ viewCourseDetails function is defined")
    else:
        print("❌ viewCourseDetails function is missing")
        return False
    
    # Test 2: Check if the function shows proper course content sections
    # Look for syllabus, slides, labs, quizzes in the function
    expected_sections = ['syllabus', 'slides', 'labs', 'quizzes']
    missing_sections = []
    
    for section in expected_sections:
        if section not in html_content.lower():
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing course content sections: {missing_sections}")
        print("   View button should show syllabus, slides, labs, and quizzes")
        return False
    else:
        print("✅ Course content sections are present in HTML")
    
    # Test 3: Check if viewCourseDetails creates proper content tabs
    if 'tab' in html_content and 'content' in html_content:
        print("✅ Tab-based content structure is present")
    else:
        print("❌ Tab-based content structure is missing")
        return False
    
    # Test 4: Check if the function actually navigates to content instead of modal
    if 'showSection(' in html_content and 'modal' in html_content:
        print("⚠️  Both section navigation and modal creation are present")
        print("   Need to check which one viewCourseDetails uses")
    
    # Test 5: Check the actual implementation of viewCourseDetails
    start_marker = 'function viewCourseDetails('
    end_marker = '}'
    
    start_pos = html_content.find(start_marker)
    if start_pos == -1:
        print("❌ Cannot find viewCourseDetails function implementation")
        return False
    
    # Find the end of the function
    brace_count = 0
    func_start = start_pos
    for i in range(func_start, len(html_content)):
        if html_content[i] == '{':
            brace_count += 1
        elif html_content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                func_end = i + 1
                break
    else:
        print("❌ Cannot find end of viewCourseDetails function")
        return False
    
    function_body = html_content[func_start:func_end]
    
    # Analyze what the function actually does
    if 'createElement' in function_body and 'modal' in function_body:
        print("❌ viewCourseDetails creates a modal (incorrect behavior)")
        print("   Expected: Navigate to course content with tabs")
        print("   Actual: Shows basic modal with course info")
        return False
    elif 'showSection(' in function_body or 'showCourseContentView(' in function_body:
        print("✅ viewCourseDetails navigates to a section (correct behavior)")
    else:
        print("❌ viewCourseDetails doesn't navigate anywhere")
        return False
    
    return True

def test_course_content_sections():
    """Test that course content sections exist and are properly structured"""
    print("\n🧪 Testing Course Content Sections")
    print("=" * 40)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for content section tabs
    content_tabs = [
        'syllabus',
        'slides', 
        'labs',
        'quizzes'
    ]
    
    all_present = True
    for tab in content_tabs:
        # Check for tab button
        tab_patterns = [
            f'onclick="showContentTab(\'{tab}\')"',
            f'data-tab="{tab}"',
            f'#{tab}-tab',
            f'id="{tab}-content"'
        ]
        
        found = any(pattern in html_content for pattern in tab_patterns)
        if found:
            print(f"✅ {tab.capitalize()} tab/content is present")
        else:
            print(f"❌ {tab.capitalize()} tab/content is missing")
            all_present = False
    
    return all_present

def test_view_button_integration():
    """Test that view button integrates properly with course content"""
    print("\n🧪 Testing View Button Integration")
    print("=" * 40)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Test that view button calls viewCourseDetails
    if 'onclick="viewCourseDetails(' in html_content:
        print("✅ View button calls viewCourseDetails function")
    else:
        print("❌ View button doesn't call viewCourseDetails")
        return False
    
    # Test that there's a way to get back to courses
    if 'showSection(\'courses\')' in html_content:
        print("✅ Navigation back to courses is available")
    else:
        print("❌ No way to navigate back to courses")
        return False
    
    return True

def test_expected_behavior():
    """Test what should happen when view button is clicked"""
    print("\n🧪 Testing Expected View Button Behavior")
    print("=" * 40)
    
    print("Expected behavior when clicking View button:")
    print("1. Should navigate to content section")
    print("2. Should show course-specific content")
    print("3. Should have tabs for: Syllabus, Slides, Labs, Quizzes")
    print("4. Should have back button to return to courses")
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check current behavior
    if 'createElement' in html_content and 'modal' in html_content:
        print("\n❌ Current behavior: Shows modal popup")
        print("   This is incorrect - should navigate to content view")
        return False
    
    print("\n✅ Expected behavior should be implemented")
    return True

def main():
    """Run all view button tests"""
    print("🚀 VIEW BUTTON FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Run all tests
    test_results = [
        test_view_button_functionality(),
        test_course_content_sections(),
        test_view_button_integration(),
        test_expected_behavior()
    ]
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 VIEW BUTTON TEST SUMMARY")
    print("=" * 35)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ View button functionality is working correctly!")
        print("   User will see course content with proper tabs")
    else:
        print("❌ View button functionality needs fixing!")
        print("   User currently sees basic modal instead of course content")
        
        print("\n🔧 REQUIRED FIXES:")
        print("1. Change viewCourseDetails to navigate to content section")
        print("2. Add course-specific content display") 
        print("3. Add tabs for Syllabus, Slides, Labs, Quizzes")
        print("4. Remove modal creation from viewCourseDetails")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)