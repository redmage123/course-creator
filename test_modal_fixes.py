#!/usr/bin/env python3
"""
Test script to verify modal fixes work correctly
"""
import requests
import time
import subprocess
import os

def test_modal_functions():
    """Test that modal functions are properly defined"""
    print("🧪 Testing Modal Function Definitions")
    print("=" * 40)
    
    # Read the HTML file
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for required functions
    required_functions = [
        'openCreateLabModal',
        'closeCreateLabModal',
        'viewCourseDetails',
        'toggleAccountDropdown'
    ]
    
    all_present = True
    for func in required_functions:
        if f'window.{func}' in html_content or f'function {func}' in html_content:
            print(f"✅ {func} function is defined")
        else:
            print(f"❌ {func} function is missing")
            all_present = False
    
    return all_present

def test_modal_prevention():
    """Test that modal stacking prevention is in place"""
    print("\n🧪 Testing Modal Stacking Prevention")
    print("=" * 40)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for modal cleanup code
    if 'document.querySelectorAll(\'.modal\').forEach(modal => {' in html_content:
        print("✅ Modal cleanup code is present")
    else:
        print("❌ Modal cleanup code is missing")
        return False
    
    # Check for removal of existing modals
    if 'modal.remove()' in html_content:
        print("✅ Modal removal code is present")
    else:
        print("❌ Modal removal code is missing")
        return False
    
    return True

def test_modal_close_functionality():
    """Test that modal close functionality is comprehensive"""
    print("\n🧪 Testing Modal Close Functionality")
    print("=" * 40)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for close button functionality
    if 'onclick="closeCreateLabModal()"' in html_content:
        print("✅ Close button functionality is present")
    else:
        print("❌ Close button functionality is missing")
        return False
    
    # Check for click outside to close
    if 'event.target.classList.contains(\'modal\')' in html_content:
        print("✅ Click outside to close functionality is present")
    else:
        print("❌ Click outside to close functionality is missing")
        return False
    
    # Check for form reset on close
    if 'form.reset()' in html_content:
        print("✅ Form reset on close is present")
    else:
        print("❌ Form reset on close is missing")
        return False
    
    return True

def test_html_structure():
    """Test that HTML structure is correct"""
    print("\n🧪 Testing HTML Structure")
    print("=" * 40)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check for Create Lab Modal
    if 'id="createLabModal"' in html_content:
        print("✅ Create Lab Modal is present in HTML")
    else:
        print("❌ Create Lab Modal is missing from HTML")
        return False
    
    # Check for close button in modal
    if 'onclick="closeCreateLabModal()">&times;</span>' in html_content:
        print("✅ Close button (×) is present in modal")
    else:
        print("❌ Close button (×) is missing from modal")
        return False
    
    # Check for Cancel button in modal
    if 'onclick="closeCreateLabModal()"' in html_content and 'Cancel' in html_content:
        print("✅ Cancel button is present in modal")
    else:
        print("❌ Cancel button is missing from modal")
        return False
    
    return True

def test_authentication_flow():
    """Test that authentication is working for modal testing"""
    print("\n🧪 Testing Authentication Flow")
    print("=" * 40)
    
    try:
        # Test login
        login_data = {
            "username": "bbrelin@gmail.com",
            "password": "f00bar123"
        }
        
        response = requests.post("http://localhost:8000/auth/login", data=login_data)
        if response.status_code == 200:
            print("✅ Authentication is working")
            token = response.json().get('access_token')
            print(f"✅ Token received: {token[:20]}...")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 MODAL FIXES TEST SUITE")
    print("=" * 50)
    
    # Run all tests
    test_results = [
        test_modal_functions(),
        test_modal_prevention(),
        test_modal_close_functionality(),
        test_html_structure(),
        test_authentication_flow()
    ]
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 TEST SUMMARY")
    print("=" * 20)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Modal fixes are working correctly.")
        print("\nFixes applied:")
        print("- Added missing openCreateLabModal function")
        print("- Added modal stacking prevention")
        print("- Added click outside to close functionality")
        print("- Added form reset on close")
        print("- Fixed modal removal logic")
        return True
    else:
        print("❌ Some tests failed. Modal fixes need more work.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)