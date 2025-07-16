#!/usr/bin/env python3
"""
Test the dashboard navigation fix
"""

def test_no_automatic_redirect():
    """Test that dashboard doesn't automatically redirect to overview"""
    print("🧪 Testing Dashboard Navigation Fix")
    print("=" * 45)
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read HTML file: {e}")
        return False
    
    # Check that showSection('overview') is NOT called automatically
    if "showSection('overview');" in content:
        print("❌ Automatic redirect to overview still exists")
        return False
    else:
        print("✅ Automatic redirect to overview removed")
    
    # Check that overview section doesn't have active class by default
    if 'id="overview-section" class="content-section active"' in content:
        print("❌ Overview section still has active class by default")
        return False
    else:
        print("✅ Overview section doesn't have active class by default")
    
    # Check that overview nav link doesn't have active class by default
    if 'data-section="overview"' in content:
        # Find the line with overview navigation
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'data-section="overview"' in line:
                if 'class="nav-link active"' in line:
                    print("❌ Overview nav link still has active class")
                    return False
                else:
                    print("✅ Overview nav link doesn't have active class")
                break
    
    # Check that the comment indicates natural navigation
    if "let user navigate naturally" in content:
        print("✅ Code indicates natural navigation approach")
    else:
        print("❌ No indication of natural navigation")
        return False
    
    print("✅ Dashboard navigation fix is complete")
    return True

def test_sections_exist():
    """Test that all sections still exist and can be navigated to"""
    print("\n🧪 Testing Section Availability")
    print("=" * 45)
    
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read HTML file: {e}")
        return False
    
    # Check that key sections exist
    sections = [
        'overview-section',
        'courses-section',
        'create-course-section',
        'students-section',
        'content-section'
    ]
    
    missing_sections = []
    for section in sections:
        if f'id="{section}"' in content:
            print(f"✅ {section} exists")
        else:
            missing_sections.append(section)
            print(f"❌ {section} missing")
    
    if missing_sections:
        print(f"❌ Missing sections: {missing_sections}")
        return False
    
    print("✅ All sections are available")
    return True

def main():
    """Run all tests"""
    print("🚀 TESTING DASHBOARD NAVIGATION FIX")
    print("=" * 50)
    
    test1 = test_no_automatic_redirect()
    test2 = test_sections_exist()
    
    if test1 and test2:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 What should work now:")
        print("• Dashboard loads without automatic redirect")
        print("• You see the main dashboard layout first")
        print("• You can manually click 'Overview' to see overview")
        print("• You can manually click 'My Courses' to see courses")
        print("• No forced navigation - user controls the experience")
        print("• All sections are still available for navigation")
        return True
    else:
        print("\n❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)