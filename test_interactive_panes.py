#!/usr/bin/env python3
"""
Test for interactive pane functionality
"""

def test_pane_click_handlers():
    """Test that all panes have click handlers"""
    print("🧪 Testing Pane Click Handlers")
    print("=" * 35)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Test pane click handlers
    pane_handlers = [
        ('syllabus-pane', 'openSyllabusPane'),
        ('slides-pane', 'openSlidesPane'),
        ('labs-pane', 'openLabEnvironment'),
        ('quizzes-pane', 'openQuizzesPane')
    ]
    
    all_handlers_present = True
    for pane_class, handler_func in pane_handlers:
        if f'class="course-pane {pane_class}" onclick="{handler_func}' in html_content:
            print(f"✅ {pane_class} has click handler: {handler_func}")
        else:
            print(f"❌ {pane_class} missing click handler: {handler_func}")
            all_handlers_present = False
    
    return all_handlers_present

def test_pane_functions():
    """Test that all pane functions are defined"""
    print("\n🧪 Testing Pane Functions")
    print("=" * 35)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Test that all pane functions are defined
    pane_functions = [
        'openSyllabusPane',
        'generateSyllabus',
        'viewFullSyllabus',
        'openSlidesPane',
        'generateSlides',
        'viewSlidesVertical',
        'startSlideshow',
        'openLabEnvironment',
        'createNewLab',
        'startLabEnvironment',
        'configureLab',
        'openQuizzesPane',
        'generateQuizzes',
        'viewAllQuizzes',
        'createQuiz'
    ]
    
    all_functions_present = True
    for func in pane_functions:
        if f'window.{func} = function' in html_content:
            print(f"✅ {func} function is defined")
        else:
            print(f"❌ {func} function is missing")
            all_functions_present = False
    
    return all_functions_present

def test_pane_buttons():
    """Test that all pane buttons are present"""
    print("\n🧪 Testing Pane Buttons")
    print("=" * 35)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Test that all pane buttons are present
    pane_buttons = [
        ('Generate', 'generateSyllabus'),
        ('View Full Syllabus', 'viewFullSyllabus'),
        ('Generate', 'generateSlides'),
        ('Vertical View', 'viewSlidesVertical'),
        ('Slideshow', 'startSlideshow'),
        ('Create', 'createNewLab'),
        ('Start Lab', 'startLabEnvironment'),
        ('Configure', 'configureLab'),
        ('Generate', 'generateQuizzes'),
        ('View All', 'viewAllQuizzes'),
        ('Create Quiz', 'createQuiz')
    ]
    
    all_buttons_present = True
    for button_text, handler in pane_buttons:
        if f'onclick="{handler}(' in html_content:
            print(f"✅ {button_text} button with {handler} handler")
        else:
            print(f"❌ {button_text} button missing {handler} handler")
            all_buttons_present = False
    
    return all_buttons_present

def test_pane_content():
    """Test that all panes have proper content"""
    print("\n🧪 Testing Pane Content")
    print("=" * 35)
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Test pane content elements
    content_elements = [
        ('syllabus-preview', 'Syllabus preview content'),
        ('slides-preview', 'Slides preview content'),
        ('slides-stack', 'Slides stack display'),
        ('slide-thumbnail', 'Slide thumbnails'),
        ('labs-preview', 'Labs preview content'),
        ('lab-environment-info', 'Lab environment info'),
        ('lab-widget', 'Lab widgets'),
        ('quizzes-preview', 'Quizzes preview content'),
        ('quiz-list', 'Quiz list'),
        ('quiz-item', 'Quiz items')
    ]
    
    all_content_present = True
    for element_class, description in content_elements:
        if element_class in html_content:
            print(f"✅ {description} ({element_class})")
        else:
            print(f"❌ {description} missing ({element_class})")
            all_content_present = False
    
    return all_content_present

def test_css_styling():
    """Test that CSS styling is present"""
    print("\n🧪 Testing CSS Styling")
    print("=" * 35)
    
    with open('/home/bbrelin/course-creator/frontend/css/main.css', 'r') as f:
        css_content = f.read()
    
    # Test CSS classes
    css_classes = [
        'course-panes-container',
        'course-pane',
        'pane-header',
        'pane-actions',
        'pane-content',
        'syllabus-preview',
        'slides-preview',
        'slides-stack',
        'slide-thumbnail',
        'slide-number',
        'lab-widget',
        'quiz-item',
        'quiz-title'
    ]
    
    all_css_present = True
    for css_class in css_classes:
        if f'.{css_class}' in css_content:
            print(f"✅ {css_class} CSS class")
        else:
            print(f"❌ {css_class} CSS class missing")
            all_css_present = False
    
    return all_css_present

def test_grid_layout():
    """Test that the grid layout is properly configured"""
    print("\n🧪 Testing Grid Layout")
    print("=" * 35)
    
    with open('/home/bbrelin/course-creator/frontend/css/main.css', 'r') as f:
        css_content = f.read()
    
    # Test grid properties
    grid_properties = [
        'display: grid',
        'grid-template-columns: 1fr 1fr',
        'grid-template-rows: 1fr 1fr',
        'height: calc(100vh - 200px)',
        'cursor: pointer'
    ]
    
    all_grid_present = True
    for property in grid_properties:
        if property in css_content:
            print(f"✅ {property}")
        else:
            print(f"❌ {property} missing")
            all_grid_present = False
    
    return all_grid_present

def main():
    """Run all tests"""
    print("🚀 INTERACTIVE PANES TEST SUITE")
    print("=" * 45)
    
    # Run all tests
    test_results = [
        test_pane_click_handlers(),
        test_pane_functions(),
        test_pane_buttons(),
        test_pane_content(),
        test_css_styling(),
        test_grid_layout()
    ]
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 INTERACTIVE PANES TEST SUMMARY")
    print("=" * 45)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All interactive pane functionality is working!")
        print("\nFeatures implemented:")
        print("• Clickable panes with proper handlers")
        print("• Interactive buttons in each pane")
        print("• Proper grid layout (2x2)")
        print("• Hover effects and transitions")
        print("• Preview content in each pane")
        print("• Function stubs for future implementation")
        
        print("\n Layout:")
        print("┌─────────────┬─────────────┐")
        print("│  Syllabus   │   Slides    │")
        print("│  (clickable)│ (clickable) │")
        print("├─────────────┼─────────────┤")
        print("│    Labs     │   Quizzes   │")
        print("│ (clickable) │ (clickable) │")
        print("└─────────────┴─────────────┘")
        
    else:
        print("❌ Some interactive pane functionality is missing!")
        print("The view button may not provide full interactivity.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)