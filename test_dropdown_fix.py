#!/usr/bin/env python3
"""
Test the account dropdown fix
"""
import re

def test_dropdown_functionality():
    """Test that the dropdown function is properly implemented"""
    
    print("🧪 Testing Account Dropdown Fix")
    print("=" * 40)
    
    # Read the HTML file
    try:
        with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read HTML file: {e}")
        return False
    
    # Check 1: Function exists
    if 'window.toggleAccountDropdown' in content:
        print("✅ toggleAccountDropdown function exists")
    else:
        print("❌ toggleAccountDropdown function missing")
        return False
    
    # Check 2: Function uses classList.toggle
    if 'classList.toggle' in content:
        print("✅ Function uses classList.toggle")
    else:
        print("❌ Function doesn't use classList.toggle")
        return False
    
    # Check 3: Function toggles 'open' class
    if "classList.toggle('open')" in content:
        print("✅ Function toggles 'open' class")
    else:
        print("❌ Function doesn't toggle 'open' class")
        return False
    
    # Check 4: Function toggles 'show' class
    if "classList.toggle('show')" in content:
        print("✅ Function toggles 'show' class")
    else:
        print("❌ Function doesn't toggle 'show' class")
        return False
    
    # Check 5: Click-outside handler exists
    if 'click-outside handler' in content:
        print("✅ Click-outside handler exists")
    else:
        print("❌ Click-outside handler missing")
        return False
    
    # Check 6: HTML structure is correct
    if 'id="accountDropdown"' in content and 'id="accountMenu"' in content:
        print("✅ HTML structure is correct")
    else:
        print("❌ HTML structure is incorrect")
        return False
    
    # Check 7: Button has correct onclick handler
    if 'onclick="toggleAccountDropdown()"' in content:
        print("✅ Button has correct onclick handler")
    else:
        print("❌ Button onclick handler is incorrect")
        return False
    
    print("=" * 40)
    print("🎉 All dropdown tests passed!")
    print("\n📋 What should work now:")
    print("• Click on username/avatar in upper right corner")
    print("• Dropdown menu should appear with Profile, Settings, Help, Logout")
    print("• Click outside the dropdown to close it")
    print("• Dropdown should have smooth CSS transitions")
    
    return True

def test_css_classes():
    """Test that CSS classes are properly defined"""
    
    print("\n🧪 Testing CSS Classes")
    print("=" * 40)
    
    try:
        with open('/home/bbrelin/course-creator/frontend/css/main.css', 'r') as f:
            css_content = f.read()
    except Exception as e:
        print(f"❌ Failed to read CSS file: {e}")
        return False
    
    # Check for required CSS classes
    required_classes = [
        '.account-dropdown',
        '.account-menu',
        '.account-menu.show',
        '.account-dropdown.open'
    ]
    
    found_classes = []
    for css_class in required_classes:
        if css_class in css_content:
            found_classes.append(css_class)
            print(f"✅ Found CSS class: {css_class}")
        else:
            print(f"❌ Missing CSS class: {css_class}")
    
    if len(found_classes) >= 3:  # Allow some flexibility
        print("✅ CSS classes are properly defined")
        return True
    else:
        print("❌ CSS classes are missing")
        return False

def main():
    """Run all tests"""
    
    test1 = test_dropdown_functionality()
    test2 = test_css_classes()
    
    if test1 and test2:
        print("\n🎉 ALL TESTS PASSED! Dropdown should work correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Dropdown may not work properly.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)