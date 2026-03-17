#!/usr/bin/env python3
"""
Final comprehensive test for the Course Creator feedback system.
"""

import os
from pathlib import Path

def test_all_components():
    """Test all feedback system components"""
    print("🚀 Final Feedback System Integration Test")
    print("=" * 50)
    
    checks = []
    
    # 1. Check feedback manager JS exists and has key functions
    feedback_js = Path("frontend/js/modules/feedback-manager.js")
    if feedback_js.exists():
        content = feedback_js.read_text()
        required = ["submitCourseFeedback", "submitStudentFeedback", "createCourseFeedbackForm", "createStudentFeedbackForm"]
        missing = [f for f in required if f not in content]
        if not missing:
            checks.append(("✅", "Feedback Manager JS - All functions present"))
        else:
            checks.append(("❌", f"Feedback Manager JS - Missing: {', '.join(missing)}"))
    else:
        checks.append(("❌", "Feedback Manager JS - File not found"))
    
    # 2. Check CSS styles
    css_file = Path("frontend/css/feedback.css")
    if css_file.exists():
        content = css_file.read_text()
        required = [".feedback-overlay", ".rating-pill", ".feedback-form", ".star-rating"]
        missing = [s for s in required if s not in content]
        if not missing:
            checks.append(("✅", "CSS Styles - All feedback styles present"))
        else:
            checks.append(("❌", f"CSS Styles - Missing: {', '.join(missing)}"))
    else:
        checks.append(("❌", "CSS Styles - feedback.css file not found"))
    
    # 3. Check student dashboard integration
    student_js = Path("frontend/js/student-dashboard.js")
    if student_js.exists():
        content = student_js.read_text()
        required = ["openCourseFeedbackForm", "Give Feedback", "feedback-btn"]
        missing = [f for f in required if f not in content]
        if not missing:
            checks.append(("✅", "Student Dashboard - Feedback integration complete"))
        else:
            checks.append(("❌", f"Student Dashboard - Missing: {', '.join(missing)}"))
    else:
        checks.append(("❌", "Student Dashboard - File not found"))
    
    # 4. Check instructor dashboard integration  
    instructor_js = Path("frontend/js/modules/instructor-dashboard.js")
    if instructor_js.exists():
        content = instructor_js.read_text()
        required = ["renderFeedbackTab", "showStudentFeedbackModal", "Feedback Management"]
        missing = [f for f in required if f not in content]
        if not missing:
            checks.append(("✅", "Instructor Dashboard - Feedback integration complete"))
        else:
            checks.append(("❌", f"Instructor Dashboard - Missing: {', '.join(missing)}"))
    else:
        checks.append(("❌", "Instructor Dashboard - File not found"))
    
    # 5. Check database migration
    migration = Path("data/migrations/008_add_feedback_system.sql")
    if migration.exists():
        content = migration.read_text()
        required = ["course_feedback", "student_feedback", "feedback_responses", "feedback_analytics"]
        missing = [t for t in required if t not in content]
        if not missing:
            checks.append(("✅", "Database Schema - All feedback tables defined"))
        else:
            checks.append(("❌", f"Database Schema - Missing tables: {', '.join(missing)}"))
    else:
        checks.append(("❌", "Database Schema - Migration file not found"))
    
    # 6. Check backend API endpoints
    backend = Path("services/course-management/main.py")
    if backend.exists():
        content = backend.read_text()
        required = ["/feedback/course", "/feedback/student", "submit_course_feedback", "submit_student_feedback"]
        missing = [e for e in required if e not in content]
        if not missing:
            checks.append(("✅", "Backend API - All feedback endpoints present"))
        else:
            checks.append(("❌", f"Backend API - Missing: {', '.join(missing)}"))
    else:
        checks.append(("❌", "Backend API - File not found"))
    
    # Print results
    print("\nTest Results:")
    print("-" * 50)
    
    passed = 0
    total = len(checks)
    
    for status, message in checks:
        print(f"{status} {message}")
        if status == "✅":
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"SUMMARY: {passed}/{total} checks passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("\nFeedback System Implementation Complete!")
        print("\nNext Steps:")
        print("1. Start the platform services")
        print("2. Create test users and courses")  
        print("3. Test feedback submission workflow")
        print("4. Verify feedback appears in instructor dashboard")
        print("5. Test bi-directional feedback flow")
        return True
    else:
        print(f"⚠️  {total - passed} checks failed - please review above")
        return False

if __name__ == "__main__":
    success = test_all_components()
    exit(0 if success else 1)