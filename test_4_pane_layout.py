#!/usr/bin/env python3
"""
Test for 4-pane layout functionality
"""

def test_4_pane_layout():
    """Test that the 4-pane layout is correctly implemented"""
    print("🧪 Testing 4-Pane Layout")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Test 1: Check for 4-pane container
    if 'course-panes-container' in html_content:
        print("✅ Course panes container is present")
    else:
        print("❌ Course panes container is missing")
        return False
    
    # Test 2: Check for two rows
    if 'course-panes-row' in html_content:
        row_count = html_content.count('course-panes-row')
        if row_count == 2:
            print("✅ Two pane rows are present")
        else:
            print(f"❌ Expected 2 pane rows, found {row_count}")
            return False
    else:
        print("❌ Course panes rows are missing")
        return False
    
    # Test 3: Check for 4 panes
    panes = ['syllabus-pane', 'slides-pane', 'labs-pane', 'quizzes-pane']
    all_panes_present = True
    
    for pane in panes:
        if pane in html_content:
            print(f"✅ {pane.replace('-', ' ').title()} is present")
        else:
            print(f"❌ {pane.replace('-', ' ').title()} is missing")
            all_panes_present = False
    
    if not all_panes_present:
        return False
    
    # Test 4: Check for pane headers
    pane_headers = ['Syllabus', 'Slides', 'Labs', 'Quizzes']
    all_headers_present = True
    
    for header in pane_headers:
        if f'<h3><i class="fas fa-' in html_content and header in html_content:
            print(f"✅ {header} pane header is present")
        else:
            print(f"❌ {header} pane header is missing")
            all_headers_present = False
    
    if not all_headers_present:
        return False
    
    # Test 5: Check for proper positioning
    # Top row should have syllabus and slides
    syllabus_pos = html_content.find('syllabus-pane')
    slides_pos = html_content.find('slides-pane')
    labs_pos = html_content.find('labs-pane')
    quizzes_pos = html_content.find('quizzes-pane')
    
    if syllabus_pos < slides_pos < labs_pos < quizzes_pos:
        print("✅ Panes are in correct order (Syllabus, Slides, Labs, Quizzes)")
    else:
        print("❌ Panes are not in correct order")
        return False
    
    return True

def test_4_pane_css():
    """Test that the CSS for 4-pane layout is present"""
    print("\n🧪 Testing 4-Pane CSS")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/css/main.css', 'r') as f:
        css_content = f.read()
    
    # Required CSS classes
    required_classes = [
        'course-panes-container',
        'course-panes-row',
        'course-pane',
        'pane-header',
        'pane-content'
    ]
    
    all_classes_present = True
    for css_class in required_classes:
        if f'.{css_class}' in css_content:
            print(f"✅ {css_class} CSS class is defined")
        else:
            print(f"❌ {css_class} CSS class is missing")
            all_classes_present = False
    
    if not all_classes_present:
        return False
    
    # Test for flexbox layout
    if 'display: flex' in css_content:
        print("✅ Flexbox layout is used")
    else:
        print("❌ Flexbox layout is missing")
        return False
    
    # Test for height constraints
    if 'height: 80vh' in css_content or 'height:80vh' in css_content:
        print("✅ Height constraint is set")
    else:
        print("❌ Height constraint is missing")
        return False
    
    return True

def test_no_tabs():
    """Test that tab functionality is removed"""
    print("\n🧪 Testing Tab Removal")
    print("=" * 30)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Check that tab-related elements are removed
    if 'course-content-tabs' in html_content:
        print("❌ Tab container still present")
        return False
    else:
        print("✅ Tab container removed")
    
    if 'showCourseContentTab' in html_content:
        print("❌ Tab function still present")
        return False
    else:
        print("✅ Tab function removed")
    
    if 'showCourseContentTab' in html_content:
        print("❌ Course content tab buttons still present")
        return False
    else:
        print("✅ Course content tab buttons removed")
    
    return True

def main():
    """Run all tests"""
    print("🚀 4-PANE LAYOUT TEST SUITE")
    print("=" * 40)
    
    # Run all tests
    test_results = [
        test_4_pane_layout(),
        test_4_pane_css(),
        test_no_tabs()
    ]
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 4-PANE LAYOUT TEST SUMMARY")
    print("=" * 35)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ 4-pane layout is working correctly!")
        print("\nLayout structure:")
        print("┌─────────────┬─────────────┐")
        print("│  Syllabus   │   Slides    │")
        print("├─────────────┼─────────────┤")
        print("│    Labs     │   Quizzes   │")
        print("└─────────────┴─────────────┘")
    else:
        print("❌ 4-pane layout has issues!")
        print("The view button may not show proper panes.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)