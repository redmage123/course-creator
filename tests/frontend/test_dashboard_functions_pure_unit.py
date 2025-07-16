"""
Pure unit tests for instructor dashboard functions without browser dependency
Tests function definitions and logic through static analysis
"""
import pytest
import re
import json
import os

class TestDashboardFunctionsPure:
    """Pure unit tests for dashboard functions"""
    
    @pytest.fixture
    def dashboard_html(self):
        """Load dashboard HTML content"""
        html_path = '/home/bbrelin/course-creator/frontend/instructor-dashboard.html'
        with open(html_path, 'r') as f:
            return f.read()
    
    def test_view_course_details_function_definition(self, dashboard_html):
        """Unit test: viewCourseDetails function is properly defined"""
        
        # Check function is defined
        assert 'function viewCourseDetails' in dashboard_html, "viewCourseDetails function should be defined"
        
        # Check it takes courseId parameter
        function_match = re.search(r'function viewCourseDetails\(([^)]+)\)', dashboard_html)
        assert function_match, "viewCourseDetails should have parameters"
        assert 'courseId' in function_match.group(1), "viewCourseDetails should take courseId parameter"
        
        # Check function is made globally available
        assert 'window.viewCourseDetails = viewCourseDetails' in dashboard_html, "viewCourseDetails should be globally available"
        
        print("✅ viewCourseDetails function is properly defined")
    
    def test_view_course_details_function_logic(self, dashboard_html):
        """Unit test: viewCourseDetails function contains correct logic"""
        
        # Extract the function body
        function_start = dashboard_html.find('function viewCourseDetails(')
        function_end = dashboard_html.find('        }', function_start) + 9
        function_body = dashboard_html[function_start:function_end]
        
        # Check for required logic
        assert 'userCourses.find' in function_body, "Should find course in userCourses"
        assert 'createElement' in function_body, "Should create modal element"
        assert 'modal-content' in function_body, "Should create modal content"
        assert 'modal-header' in function_body, "Should create modal header"
        assert 'modal-body' in function_body, "Should create modal body"
        assert 'modal-footer' in function_body, "Should create modal footer"
        assert 'appendChild' in function_body, "Should append modal to document"
        
        print("✅ viewCourseDetails function contains correct logic")
    
    def test_confirm_delete_course_function_definition(self, dashboard_html):
        """Unit test: confirmDeleteCourse function is properly defined"""
        
        assert 'function confirmDeleteCourse' in dashboard_html, "confirmDeleteCourse function should be defined"
        
        # Check it takes courseId parameter
        function_match = re.search(r'function confirmDeleteCourse\(([^)]+)\)', dashboard_html)
        assert function_match, "confirmDeleteCourse should have parameters"
        assert 'courseId' in function_match.group(1), "confirmDeleteCourse should take courseId parameter"
        
        # Check function is made globally available
        assert 'window.confirmDeleteCourse = confirmDeleteCourse' in dashboard_html, "confirmDeleteCourse should be globally available"
        
        print("✅ confirmDeleteCourse function is properly defined")
    
    def test_confirm_delete_course_function_logic(self, dashboard_html):
        """Unit test: confirmDeleteCourse function contains correct logic"""
        
        # Extract the function body
        function_start = dashboard_html.find('function confirmDeleteCourse(')
        function_end = dashboard_html.find('        }', function_start) + 9
        function_body = dashboard_html[function_start:function_end]
        
        # Check for required logic
        assert 'userCourses.find' in function_body, "Should find course in userCourses"
        assert 'confirm(' in function_body, "Should show confirmation dialog"
        assert 'deleteCourse(' in function_body, "Should call deleteCourse function"
        
        print("✅ confirmDeleteCourse function contains correct logic")
    
    def test_delete_course_function_definition(self, dashboard_html):
        """Unit test: deleteCourse function is properly defined"""
        
        assert 'function deleteCourse' in dashboard_html, "deleteCourse function should be defined"
        assert 'async function deleteCourse' in dashboard_html, "deleteCourse should be async"
        
        # Check function is made globally available
        assert 'window.deleteCourse = deleteCourse' in dashboard_html, "deleteCourse should be globally available"
        
        print("✅ deleteCourse function is properly defined")
    
    def test_delete_course_function_logic(self, dashboard_html):
        """Unit test: deleteCourse function contains correct logic"""
        
        # Extract the function body
        function_start = dashboard_html.find('async function deleteCourse(')
        function_end = dashboard_html.find('        }', function_start) + 9
        function_body = dashboard_html[function_start:function_end]
        
        # Check for required logic
        assert 'fetch(' in function_body, "Should make fetch request"
        assert 'DELETE' in function_body, "Should use DELETE method"
        assert 'Authorization' in function_body, "Should include authorization header"
        assert 'userCourses.filter' in function_body, "Should remove course from local array"
        assert 'updateCoursesDisplay' in function_body, "Should update display"
        
        print("✅ deleteCourse function contains correct logic")
    
    def test_update_courses_display_function_definition(self, dashboard_html):
        """Unit test: updateCoursesDisplay function is properly defined"""
        
        assert 'function updateCoursesDisplay' in dashboard_html, "updateCoursesDisplay function should be defined"
        
        # Check function is made globally available
        assert 'window.updateCoursesDisplay = updateCoursesDisplay' in dashboard_html, "updateCoursesDisplay should be globally available"
        
        print("✅ updateCoursesDisplay function is properly defined")
    
    def test_update_courses_display_function_logic(self, dashboard_html):
        """Unit test: updateCoursesDisplay function contains correct logic"""
        
        # Extract the function body
        function_start = dashboard_html.find('function updateCoursesDisplay(')
        function_end = dashboard_html.find('        }', function_start) + 9
        function_body = dashboard_html[function_start:function_end]
        
        # Check for required logic
        assert 'getElementById(\'courses-list\')' in function_body, "Should find courses-list element"
        assert 'userCourses.map' in function_body, "Should map over userCourses"
        assert 'course-card enhanced' in function_body, "Should create enhanced course cards"
        assert 'course-header' in function_body, "Should create course header"
        assert 'course-body' in function_body, "Should create course body"
        assert 'course-actions' in function_body, "Should create course actions"
        assert 'viewCourseDetails' in function_body, "Should reference viewCourseDetails"
        assert 'confirmDeleteCourse' in function_body, "Should reference confirmDeleteCourse"
        
        print("✅ updateCoursesDisplay function contains correct logic")
    
    def test_show_section_function_definition(self, dashboard_html):
        """Unit test: showSection function is properly defined"""
        
        assert 'function showSection' in dashboard_html, "showSection function should be defined"
        assert 'window.showSection = function' in dashboard_html, "showSection should be globally available"
        
        print("✅ showSection function is properly defined")
    
    def test_show_section_function_logic(self, dashboard_html):
        """Unit test: showSection function contains correct logic"""
        
        # Extract the function body
        function_start = dashboard_html.find('window.showSection = function(')
        function_end = dashboard_html.find('        };', function_start) + 10
        function_body = dashboard_html[function_start:function_end]
        
        # Check for required logic
        assert 'querySelectorAll(\'.content-section\')' in function_body, "Should find all content sections"
        assert 'classList.remove(\'active\')' in function_body, "Should remove active class"
        assert 'classList.add(\'active\')' in function_body, "Should add active class"
        assert 'getElementById(sectionName + \'-section\')' in function_body, "Should find target section"
        assert 'updateCoursesDisplay' in function_body, "Should update courses display for courses section"
        
        print("✅ showSection function contains correct logic")
    
    def test_close_create_lab_modal_function_definition(self, dashboard_html):
        """Unit test: closeCreateLabModal function is properly defined (fixes original error)"""
        
        assert 'function closeCreateLabModal' in dashboard_html, "closeCreateLabModal function should be defined"
        assert 'window.closeCreateLabModal' in dashboard_html, "closeCreateLabModal should be globally available"
        
        print("✅ closeCreateLabModal function is properly defined (original error fixed)")
    
    def test_all_missing_functions_are_defined(self, dashboard_html):
        """Unit test: All previously missing functions are now defined"""
        
        required_functions = [
            'viewCourseDetails',
            'confirmDeleteCourse',
            'deleteCourse',
            'updateCoursesDisplay',
            'showSection',
            'closeCreateLabModal',
            'toggleAccountDropdown',
            'logout',
            'viewAnalytics',
            'resetForm',
            'openContentUploadModal',
            'filterCourses',
            'searchCourses'
        ]
        
        missing_functions = []
        for func in required_functions:
            if f'window.{func}' not in dashboard_html:
                missing_functions.append(func)
        
        assert len(missing_functions) == 0, f"Missing functions: {missing_functions}"
        
        print(f"✅ All {len(required_functions)} required functions are defined")
    
    def test_course_actions_horizontal_layout(self, dashboard_html):
        """Unit test: Course actions have horizontal layout styling"""
        
        # Check for horizontal layout styling in course actions
        assert 'display: flex; gap: 10px' in dashboard_html, "Course actions should have horizontal layout"
        
        # Check it's in the course actions div
        course_actions_match = re.search(r'<div class="course-actions"[^>]*style="([^"]*)"', dashboard_html)
        assert course_actions_match, "Course actions should have inline style"
        
        style = course_actions_match.group(1)
        assert 'display: flex' in style, "Course actions should have display: flex"
        assert 'gap: 10px' in style, "Course actions should have gap: 10px"
        
        print("✅ Course actions have horizontal layout styling")
    
    def test_modal_styling_included(self, dashboard_html):
        """Unit test: Modal styling is included in the page"""
        
        # Check for modal CSS
        modal_css_elements = [
            '.modal {',
            '.modal-content {',
            '.modal-header {',
            '.modal-body {',
            '.modal-footer {',
            '.close-btn {'
        ]
        
        missing_css = []
        for css_element in modal_css_elements:
            if css_element not in dashboard_html:
                missing_css.append(css_element)
        
        assert len(missing_css) == 0, f"Missing modal CSS: {missing_css}"
        
        print("✅ Modal styling is included in the page")
    
    def test_course_card_structure(self, dashboard_html):
        """Unit test: Course card structure is correct"""
        
        # Check for course card structure elements
        card_elements = [
            'course-card enhanced',
            'course-header',
            'course-body',
            'course-actions',
            'course-status',
            'course-meta'
        ]
        
        missing_elements = []
        for element in card_elements:
            if element not in dashboard_html:
                missing_elements.append(element)
        
        assert len(missing_elements) == 0, f"Missing course card elements: {missing_elements}"
        
        print("✅ Course card structure is correct")
    
    def test_button_onclick_handlers(self, dashboard_html):
        """Unit test: Button onclick handlers are correct"""
        
        # Check for correct onclick handlers
        onclick_handlers = [
            'onclick="viewCourseDetails(',
            'onclick="confirmDeleteCourse(',
            'onclick="showSection(\'content\')"'
        ]
        
        missing_handlers = []
        for handler in onclick_handlers:
            if handler not in dashboard_html:
                missing_handlers.append(handler)
        
        assert len(missing_handlers) == 0, f"Missing onclick handlers: {missing_handlers}"
        
        print("✅ Button onclick handlers are correct")
    
    def test_error_handling_in_functions(self, dashboard_html):
        """Unit test: Functions include proper error handling"""
        
        # Check for error handling patterns
        error_patterns = [
            'try {',
            'catch',
            'console.error',
            'showNotification.*error'
        ]
        
        found_patterns = []
        for pattern in error_patterns:
            if re.search(pattern, dashboard_html):
                found_patterns.append(pattern)
        
        # At least some error handling should be present
        assert len(found_patterns) >= 2, f"Should have error handling patterns, found: {found_patterns}"
        
        print("✅ Functions include proper error handling")
    
    def test_function_parameter_validation(self, dashboard_html):
        """Unit test: Functions validate their parameters"""
        
        # Check for parameter validation patterns
        validation_patterns = [
            'if (!course)',
            'if (!courseId)',
            'if (!.*) {',
            'course.find'
        ]
        
        found_validations = []
        for pattern in validation_patterns:
            if re.search(pattern, dashboard_html):
                found_validations.append(pattern)
        
        # At least some validation should be present
        assert len(found_validations) >= 2, f"Should have parameter validation, found: {found_validations}"
        
        print("✅ Functions include parameter validation")