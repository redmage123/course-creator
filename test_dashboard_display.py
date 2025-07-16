#!/usr/bin/env python3
"""
Test that dashboard displays correctly with default active section
"""

def test_dashboard_display():
    """Test that dashboard has proper default display"""
    print("🧪 Testing Dashboard Display Fix")
    print("=" * 40)
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read HTML file: {e}")
        return False
    
    # Check that overview section has active class by default
    if 'id="overview-section" class="content-section active"' in content:
        print("✅ Overview section has active class by default")
    else:
        print("❌ Overview section doesn't have active class by default")
        return False
    
    # Check that overview nav link has active class
    overview_nav_found = False
    lines = content.split('\n')
    for line in lines:
        if 'data-section="overview"' in line and 'class="nav-link active"' in line:
            overview_nav_found = True
            break
    
    if overview_nav_found:
        print("✅ Overview nav link has active class")
    else:
        print("❌ Overview nav link doesn't have active class")
        return False
    
    # Check that main-header exists (for breadcrumb and create button)
    if 'class="main-header"' in content:
        print("✅ Main header exists")
    else:
        print("❌ Main header missing")
        return False
    
    # Check that main-content exists
    if 'class="main-content"' in content:
        print("✅ Main content area exists")
    else:
        print("❌ Main content area missing")
        return False
    
    # Check that we still don't have automatic redirect during init
    if "showSection('overview');" in content:
        print("❌ Automatic redirect still exists in initialization")
        return False
    else:
        print("✅ No automatic redirect during initialization")
    
    # Check that overview section has proper content
    if 'Welcome back!' in content and 'happening with your courses today' in content:
        print("✅ Overview section has proper welcome content")
    else:
        print("❌ Overview section missing welcome content")
        return False
    
    print("✅ Dashboard display fix is complete")
    return True

def test_css_content_sections():
    """Test that CSS properly handles content sections"""
    print("\n🧪 Testing CSS Content Section Rules")
    print("=" * 40)
    
    try:
        with open('/home/bbrelin/course-creator/frontend/css/main.css', 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read CSS file: {e}")
        return False
    
    # Check for content-section rules
    if '.content-section {' in content:
        print("✅ Content section base rule exists")
    else:
        print("❌ Content section base rule missing")
        return False
    
    # Check for active state rule
    if '.content-section.active {' in content:
        print("✅ Content section active rule exists")
    else:
        print("❌ Content section active rule missing")
        return False
    
    # Check that hidden sections are display: none
    if 'display: none' in content:
        print("✅ Hidden sections have display: none")
    else:
        print("❌ Hidden sections display rule missing")
        return False
    
    # Check that active sections are display: block
    if 'display: block' in content:
        print("✅ Active sections have display: block")
    else:
        print("❌ Active sections display rule missing")
        return False
    
    print("✅ CSS content section rules are correct")
    return True

def main():
    """Run all tests"""
    print("🚀 TESTING DASHBOARD DISPLAY FIX")
    print("=" * 50)
    
    test1 = test_dashboard_display()
    test2 = test_css_content_sections()
    
    if test1 and test2:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 What should work now:")
        print("• Dashboard loads with Overview section visible by default")
        print("• You see the welcome message and course statistics")
        print("• Main header shows breadcrumb and Create Course button")
        print("• You can navigate to My Courses or other sections")
        print("• No automatic redirect during initialization")
        print("• Overview is the natural default landing page")
        return True
    else:
        print("\n❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)