#!/usr/bin/env python3
"""
Comprehensive test script for the Course Creator feedback system.
Tests the frontend components, CSS styling, and JavaScript integration.
"""

import os
import json
from pathlib import Path

def test_feedback_manager_js():
    """Test the feedback manager JavaScript module"""
    print("🔍 Testing Feedback Manager JavaScript Module...")
    
    feedback_manager_path = Path("frontend/js/modules/feedback-manager.js")
    if not feedback_manager_path.exists():
        print("  ❌ feedback-manager.js not found")
        return False
        
    content = feedback_manager_path.read_text()
    
    # Check for key components
    required_components = [
        "class FeedbackManager",
        "submitCourseFeedback",
        "submitStudentFeedback", 
        "getCourseFeedback",
        "getStudentFeedback",
        "createCourseFeedbackForm",
        "createStudentFeedbackForm",
        "handleCourseFeedbackSubmit",
        "handleStudentFeedbackSubmit",
        "createStarRating"
    ]
    
    missing_components = []
    for component in required_components:
        if component not in content:
            missing_components.append(component)
    
    if missing_components:
        print(f"  ❌ Missing components: {', '.join(missing_components)}")
        return False
    
    print("  ✅ All required components found")
    print(f"  📊 File size: {len(content):,} characters")
    return True

def test_feedback_css():
    """Test feedback CSS styles"""
    print("\n🎨 Testing Feedback CSS Styles...")
    
    css_path = Path("frontend/css/main.css")
    if not css_path.exists():
        print("  ❌ main.css not found")
        return False
        
    content = css_path.read_text()
    
    # Check for feedback-specific CSS classes
    required_styles = [
        ".feedback-overlay",
        ".feedback-modal", 
        ".feedback-form",
        ".star-rating",
        ".feedback-item",
        ".rating-pill",
        ".feedback-loading",
        ".feedback-notification"
    ]
    
    missing_styles = []
    for style in required_styles:
        if style not in content:
            missing_styles.append(style)
    
    if missing_styles:
        print(f"  ❌ Missing CSS styles: {', '.join(missing_styles)}")
        return False
    
    print("  ✅ All required CSS styles found")
    return True

def test_student_dashboard_integration():
    """Test student dashboard feedback integration"""
    print("\n👨‍🎓 Testing Student Dashboard Integration...")
    
    student_js_path = Path("frontend/js/student-dashboard.js")
    if not student_js_path.exists():
        print("  ❌ student-dashboard.js not found")
        return False
        
    content = student_js_path.read_text()
    
    # Check for feedback integration
    required_functions = [
        "openCourseFeedbackForm",
        "closeFeedbackForm",
        "openStudentFeedbackView",
        "closeStudentFeedbackView"
    ]
    
    integration_checks = [
        "import('./modules/feedback-manager.js')",
        "feedbackManager.createCourseFeedbackForm",
        "Give Feedback",
        "feedback-btn"
    ]
    
    missing_functions = []
    for func in required_functions:
        if func not in content:
            missing_functions.append(func)
    
    missing_integration = []
    for check in integration_checks:
        if check not in content:
            missing_integration.append(check)
    
    success = True
    if missing_functions:
        print(f"  ❌ Missing functions: {', '.join(missing_functions)}")
        success = False
    
    if missing_integration:
        print(f"  ❌ Missing integration: {', '.join(missing_integration)}")
        success = False
    
    if success:
        print("  ✅ Student dashboard feedback integration complete")
        
    return success

def test_instructor_dashboard_integration():
    """Test instructor dashboard feedback integration"""
    print("\n👨‍🏫 Testing Instructor Dashboard Integration...")
    
    instructor_js_path = Path("frontend/js/modules/instructor-dashboard.js")
    if not instructor_js_path.exists():
        print("  ❌ instructor-dashboard.js not found")
        return False
        
    content = instructor_js_path.read_text()
    
    # Check for feedback integration
    required_components = [
        "renderFeedbackTab",
        "renderCourseFeedbackSection", 
        "renderStudentFeedbackSection",
        "loadFeedbackData",
        "showStudentFeedbackModal",
        "updateCourseFeedbackDisplay",
        "renderStarRating"
    ]
    
    integration_checks = [
        "Feedback Management",
        "feedback-tab",
        "Course Feedback from Students",
        "Student Assessment Feedback",
        "feedbackManager.createStudentFeedbackForm",
        "Give Feedback"
    ]
    
    missing_components = []
    for component in required_components:
        if component not in content:
            missing_components.append(component)
    
    missing_integration = []
    for check in integration_checks:
        if check not in content:
            missing_integration.append(check)
    
    success = True
    if missing_components:
        print(f"  ❌ Missing components: {', '.join(missing_components)}")
        success = False
    
    if missing_integration:
        print(f"  ❌ Missing integration: {', '.join(missing_integration)}")
        success = False
    
    if success:
        print("  ✅ Instructor dashboard feedback integration complete")
        
    return success

def test_student_dashboard_html():
    """Test student dashboard HTML for feedback buttons"""
    print("\n📄 Testing Student Dashboard HTML...")
    
    html_path = Path("frontend/student-dashboard.html")
    if not html_path.exists():
        print("  ❌ student-dashboard.html not found")
        return False
        
    content = html_path.read_text()
    
    # Check that the HTML structure supports the JavaScript integration
    required_elements = [
        'class="courses-grid"',
        'id="student-courses-list"',
        'class="modal"',
        'type="module"'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"  ❌ Missing HTML elements: {', '.join(missing_elements)}")
        return False
    
    print("  ✅ Student dashboard HTML structure supports feedback integration")
    return True

def test_database_schema():
    """Test database schema exists"""
    print("\n🗄️  Testing Database Schema...")
    
    migration_path = Path("data/migrations/008_add_feedback_system.sql")
    if not migration_path.exists():
        print("  ❌ Feedback system migration not found")
        return False
        
    content = migration_path.read_text()
    
    # Check for required tables
    required_tables = [
        "CREATE TABLE course_feedback",
        "CREATE TABLE student_feedback",
        "CREATE TABLE feedback_responses",
        "CREATE TABLE feedback_analytics"
    ]
    
    missing_tables = []
    for table in required_tables:
        if table not in content:
            missing_tables.append(table)
    
    if missing_tables:
        print(f"  ❌ Missing database tables: {', '.join(missing_tables)}")
        return False
    
    print("  ✅ Database schema includes all feedback tables")
    print(f"  📊 Migration file size: {len(content):,} characters")
    return True

def test_backend_api_endpoints():
    """Test that backend API endpoints exist"""
    print("\n🔗 Testing Backend API Endpoints...")
    
    course_management_path = Path("services/course-management/main.py")
    if not course_management_path.exists():
        print("  ❌ course-management main.py not found")
        return False
        
    content = course_management_path.read_text()
    
    # Check for feedback API endpoints
    required_endpoints = [
        "/feedback/course",
        "/feedback/student", 
        "submit_course_feedback",
        "submit_student_feedback",
        "get_course_feedback",
        "get_student_feedback"
    ]
    
    missing_endpoints = []
    for endpoint in required_endpoints:
        if endpoint not in content:
            missing_endpoints.append(endpoint)
    
    if missing_endpoints:
        print(f"  ❌ Missing API endpoints: {', '.join(missing_endpoints)}")
        return False
    
    print("  ✅ All required API endpoints found")
    return True

def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "="*60)
    print("📋 FEEDBACK SYSTEM TEST REPORT")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Feedback system is ready for deployment.")
        print("\nNext Steps:")
        print("  1. Start the database and application services")
        print("  2. Create test users (student and instructor)")
        print("  3. Create test courses and enroll students")
        print("  4. Test the feedback workflow end-to-end")
        print("  5. Verify data persistence and retrieval")
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed. Please review and fix the issues above.")
    
    return failed_tests == 0

def main():
    """Run all feedback system tests"""
    print("🚀 Starting Feedback System Integration Tests")
    print("=" * 60)
    
    # Run all tests
    test_results = {
        "Feedback Manager JS": test_feedback_manager_js(),
        "Feedback CSS Styles": test_feedback_css(),
        "Student Dashboard Integration": test_student_dashboard_integration(),
        "Instructor Dashboard Integration": test_instructor_dashboard_integration(),
        "Student Dashboard HTML": test_student_dashboard_html(),
        "Database Schema": test_database_schema(),
        "Backend API Endpoints": test_backend_api_endpoints()
    }
    
    # Generate report
    success = generate_test_report(test_results)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())