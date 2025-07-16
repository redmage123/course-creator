#!/usr/bin/env python3
"""
Simple test to verify the redirect fix in HTML
"""

def test_html_fix():
    """Test that the HTML no longer has hardcoded active sections"""
    print("🧪 Testing HTML Fix")
    print("=" * 20)
    
    # Read the dashboard HTML
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Test 1: Check that overview section is not hardcoded as active
    if 'id="overview-section" class="content-section active"' in html_content:
        print("❌ Overview section still has hardcoded active class")
        return False
    else:
        print("✅ Overview section no longer has hardcoded active class")
    
    # Test 2: Check that overview nav link is not hardcoded as active
    if 'nav-link active" onclick="showSection(\'overview\')"' in html_content:
        print("❌ Overview nav link still has hardcoded active class")
        return False
    else:
        print("✅ Overview nav link no longer has hardcoded active class")
    
    # Test 3: Check that getCurrentUser function is defined
    if 'function getCurrentUser()' in html_content:
        print("✅ getCurrentUser function is defined")
    else:
        print("❌ getCurrentUser function is missing")
        return False
    
    # Test 4: Check that dashboard shows courses by default
    if "showSection('courses')" in html_content:
        print("✅ Dashboard is set to show courses section by default")
    else:
        print("❌ Dashboard does not show courses section by default")
        return False
    
    return True

def main():
    """Run the tests"""
    print("🚀 SIMPLE HTML FIX CHECK")
    print("=" * 30)
    
    success = test_html_fix()
    
    if success:
        print("\n✅ All HTML fixes are in place!")
        print("   The dashboard should now:")
        print("   - Not auto-redirect to overview")
        print("   - Show courses section by default")
        print("   - Have proper getCurrentUser function")
    else:
        print("\n❌ Some fixes are missing!")
        print("   The dashboard may still have issues")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)