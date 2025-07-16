"""
Simple test suite for clickable panes functionality.
Tests the implementation without requiring browser automation.
"""
import pytest
import os
import re


class TestClickablePanesSimple:
    """Test suite for clickable panes functionality without browser automation."""
    
    def test_instructor_dashboard_has_clickable_panes(self):
        """Test that instructor dashboard contains clickable panes."""
        dashboard_path = "/home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        
        # Read the instructor dashboard HTML
        with open(dashboard_path, 'r') as f:
            dashboard_html = f.read()
        
        # Check that the HTML contains clickable-pane classes
        assert "clickable-pane" in dashboard_html, "HTML should contain clickable-pane class"
        
        # Check for the specific onclick handlers that should be present
        expected_handlers = [
            'onclick="viewSyllabus(',
            'onclick="viewAllSlides(',
            'onclick="openEmbeddedLab(',
            'onclick="viewQuizzes('
        ]
        
        for handler in expected_handlers:
            assert handler in dashboard_html, f"Missing onclick handler: {handler}"
        
        # Check that pane action hints are present
        assert "pane-action-hint" in dashboard_html, "HTML should contain pane action hints"
        
        # Check that help text is present
        assert "Click on any content pane above to view" in dashboard_html, "Help text should be present"
    
    def test_instructor_dashboard_js_has_clickable_pane_functions(self):
        """Test that instructor dashboard JavaScript contains the clickable pane functions."""
        js_path = "/home/bbrelin/course-creator/frontend/js/instructor-dashboard.js"
        
        # Read the JavaScript file
        with open(js_path, 'r') as f:
            js_content = f.read()
        
        # Check for the clickable pane functions
        expected_functions = [
            'function viewSyllabus(',
            'function viewAllSlides(',
            'function openEmbeddedLab(',
            'function viewQuizzes('
        ]
        
        for func in expected_functions:
            assert func in js_content, f"Missing JavaScript function: {func}"
        
        # Check that the loadCourseContent function generates clickable panes
        assert 'class="content-card clickable-pane"' in js_content, "loadCourseContent should generate clickable panes"
    
    def test_css_has_clickable_pane_styles(self):
        """Test that CSS contains styles for clickable panes."""
        css_path = "/home/bbrelin/course-creator/frontend/css/main.css"
        
        # Read the CSS file
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        # Check for clickable pane styles
        assert ".clickable-pane" in css_content, "CSS should contain .clickable-pane styles"
        
        # Check for cursor pointer and hover effects
        assert "cursor: pointer" in css_content, "Clickable panes should have cursor pointer"
        assert "transition:" in css_content, "Clickable panes should have transition effects"
    
    def test_bottom_menu_buttons_removed(self):
        """Test that old bottom menu buttons are removed."""
        dashboard_path = "/home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        
        # Read the instructor dashboard HTML
        with open(dashboard_path, 'r') as f:
            dashboard_html = f.read()
        
        # Check that old bottom menu buttons are NOT present
        old_buttons = [
            'id="edit-content-btn"',
            'id="launch-lab-btn"',
            'id="view-quizzes-btn"',
            'class="content-actions"'
        ]
        
        for button in old_buttons:
            assert button not in dashboard_html, f"Old button should be removed: {button}"
        
        # Check that new content-info div is present instead
        assert 'class="content-info"' in dashboard_html, "Should have content-info div instead of content-actions"
    
    def test_pane_action_hints_present(self):
        """Test that pane action hints are present in the HTML."""
        dashboard_path = "/home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        
        # Read the instructor dashboard HTML
        with open(dashboard_path, 'r') as f:
            dashboard_html = f.read()
        
        # Check for pane action hints
        assert "pane-action-hint" in dashboard_html, "HTML should contain pane action hints"
        
        # Check for mouse pointer icon in hints
        assert "fa-mouse-pointer" in dashboard_html, "Action hints should have mouse pointer icon"
        
        # Check for hint text
        hint_texts = ["Click to view", "Click to launch"]
        for hint_text in hint_texts:
            assert hint_text in dashboard_html, f"Missing hint text: {hint_text}"
    
    def test_event_propagation_handling(self):
        """Test that event propagation is handled correctly for internal buttons."""
        js_path = "/home/bbrelin/course-creator/frontend/js/instructor-dashboard.js"
        
        # Read the JavaScript file
        with open(js_path, 'r') as f:
            js_content = f.read()
        
        # Check for event.stopPropagation() calls
        assert "event.stopPropagation()" in js_content, "Should have event.stopPropagation() for internal buttons"
        
        # Check for onclick handlers that stop propagation
        assert "onclick=\"event.stopPropagation()" in js_content, "Internal buttons should stop event propagation"
    
    def test_tdd_implementation_complete(self):
        """Test that the TDD implementation is complete with all required elements."""
        # Test that all required files exist
        required_files = [
            "/home/bbrelin/course-creator/frontend/instructor-dashboard.html",
            "/home/bbrelin/course-creator/frontend/js/instructor-dashboard.js",
            "/home/bbrelin/course-creator/frontend/css/main.css"
        ]
        
        for file_path in required_files:
            assert os.path.exists(file_path), f"Required file missing: {file_path}"
        
        # Test that all major components are implemented
        dashboard_path = "/home/bbrelin/course-creator/frontend/instructor-dashboard.html"
        with open(dashboard_path, 'r') as f:
            dashboard_html = f.read()
        
        # Check that the implementation follows TDD principles
        # 1. All panes are clickable (Red -> Green)
        clickable_panes = len(re.findall(r'class="[^"]*clickable-pane[^"]*"', dashboard_html))
        assert clickable_panes >= 4, "Should have at least 4 clickable panes"
        
        # 2. Old buttons are removed (Red -> Green)
        old_actions = dashboard_html.count('content-actions')
        assert old_actions == 0, "Old content-actions should be completely removed"
        
        # 3. New help text is present (Red -> Green)
        assert "content-info" in dashboard_html, "New content-info section should be present"
        
        # 4. All onclick handlers are present (Red -> Green)
        onclick_handlers = len(re.findall(r'onclick="[^"]*"', dashboard_html))
        assert onclick_handlers >= 4, "Should have at least 4 onclick handlers"