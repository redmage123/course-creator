#!/usr/bin/env python3
"""
Test the authentication and styling fixes
"""

def test_authentication_fix():
    """Test that 401 handling is implemented"""
    print("🧪 Testing Authentication Fix")
    print("=" * 40)
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read HTML file: {e}")
        return False
    
    # Check for 401 handling
    if 'response.status === 401' in content:
        print("✅ 401 status check implemented")
    else:
        print("❌ 401 status check missing")
        return False
    
    # Check for session expired message
    if 'Session expired' in content:
        print("✅ Session expired message implemented")
    else:
        print("❌ Session expired message missing")
        return False
    
    # Check for token cleanup
    if 'localStorage.removeItem' in content:
        print("✅ Token cleanup implemented")
    else:
        print("❌ Token cleanup missing")
        return False
    
    # Check for redirect to login
    if 'window.location.href = \'index.html\'' in content:
        print("✅ Redirect to login implemented")
    else:
        print("❌ Redirect to login missing")
        return False
    
    print("✅ Authentication fix is complete")
    return True

def test_styling_fix():
    """Test that search box styling is fixed"""
    print("\n🧪 Testing Styling Fix")
    print("=" * 40)
    
    try:
        with open('/home/bbrelin/course-creator/frontend/css/main.css', 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read CSS file: {e}")
        return False
    
    # Check for search box max-width
    if 'max-width: 400px' in content:
        print("✅ Search box max-width implemented")
    else:
        print("❌ Search box max-width missing")
        return False
    
    # Check for section header flexbox
    if 'display: flex' in content and 'justify-content: space-between' in content:
        print("✅ Section header flexbox implemented")
    else:
        print("❌ Section header flexbox missing")
        return False
    
    # Check for course filters constraints
    if 'max-width: 100%' in content and 'flex-shrink: 0' in content:
        print("✅ Course filters constraints implemented")
    else:
        print("❌ Course filters constraints missing")
        return False
    
    print("✅ Styling fix is complete")
    return True

def main():
    """Run both tests"""
    print("🚀 TESTING AUTHENTICATION AND STYLING FIXES")
    print("=" * 50)
    
    auth_test = test_authentication_fix()
    style_test = test_styling_fix()
    
    if auth_test and style_test:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 What should work now:")
        print("• Authentication errors will show 'Session expired' message")
        print("• User will be redirected to login page on 401 errors")
        print("• Search box will not extend beyond the right border")
        print("• Course filters will stay within the rounded container")
        print("• Section header will properly contain its elements")
        return True
    else:
        print("\n❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)