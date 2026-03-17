#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) Validation Tests

This module provides comprehensive testing for role-based access control
implementation in the Course Creator Platform, validating that access
restrictions are properly enforced across all services.
"""

import asyncio
import sys
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'services' / 'user-management'))

# Import User entity for role checking
from user_management.domain.entities.user import User, UserRole, UserStatus


class RBACValidationTest:
    """Test role-based access control implementation"""
    
    def __init__(self):
        self.results = []
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log RBAC test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.results.append({
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def test_user_role_methods(self) -> bool:
        """Test User entity role checking methods"""
        all_passed = True
        
        # Test student user
        student = User(
            email="student@test.com",
            username="student",
            full_name="Test Student",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        
        # Student should not have admin or instructor privileges
        student_admin_check = not student.is_admin()
        student_instructor_check = not student.is_instructor()
        student_create_courses = not student.can_create_courses()
        student_manage_users = not student.can_manage_users()
        
        self.log_test_result(
            "Student Role - Admin Check",
            student_admin_check,
            f"Student is_admin(): {student.is_admin()} (should be False)"
        )
        
        self.log_test_result(
            "Student Role - Instructor Check", 
            student_instructor_check,
            f"Student is_instructor(): {student.is_instructor()} (should be False)"
        )
        
        self.log_test_result(
            "Student Role - Create Courses",
            student_create_courses,
            f"Student can_create_courses(): {student.can_create_courses()} (should be False)"
        )
        
        self.log_test_result(
            "Student Role - Manage Users",
            student_manage_users,
            f"Student can_manage_users(): {student.can_manage_users()} (should be False)"
        )
        
        if not all([student_admin_check, student_instructor_check, student_create_courses, student_manage_users]):
            all_passed = False
        
        # Test instructor user
        instructor = User(
            email="instructor@test.com",
            username="instructor", 
            full_name="Test Instructor",
            role=UserRole.INSTRUCTOR,
            status=UserStatus.ACTIVE
        )
        
        # Instructor should have instructor privileges but not admin
        instructor_admin_check = not instructor.is_admin()
        instructor_instructor_check = instructor.is_instructor()
        instructor_create_courses = instructor.can_create_courses()
        instructor_manage_users = not instructor.can_manage_users()
        
        self.log_test_result(
            "Instructor Role - Admin Check",
            instructor_admin_check,
            f"Instructor is_admin(): {instructor.is_admin()} (should be False)"
        )
        
        self.log_test_result(
            "Instructor Role - Instructor Check",
            instructor_instructor_check,
            f"Instructor is_instructor(): {instructor.is_instructor()} (should be True)"
        )
        
        self.log_test_result(
            "Instructor Role - Create Courses",
            instructor_create_courses,
            f"Instructor can_create_courses(): {instructor.can_create_courses()} (should be True)"
        )
        
        self.log_test_result(
            "Instructor Role - Manage Users",
            instructor_manage_users,
            f"Instructor can_manage_users(): {instructor.can_manage_users()} (should be False)"
        )
        
        if not all([instructor_admin_check, instructor_instructor_check, instructor_create_courses, instructor_manage_users]):
            all_passed = False
        
        # Test admin user
        admin = User(
            email="admin@test.com",
            username="admin",
            full_name="Test Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
        
        # Admin should have all privileges
        admin_admin_check = admin.is_admin()
        admin_instructor_check = admin.is_instructor()
        admin_create_courses = admin.can_create_courses()
        admin_manage_users = admin.can_manage_users()
        
        self.log_test_result(
            "Admin Role - Admin Check",
            admin_admin_check,
            f"Admin is_admin(): {admin.is_admin()} (should be True)"
        )
        
        self.log_test_result(
            "Admin Role - Instructor Check",
            admin_instructor_check,
            f"Admin is_instructor(): {admin.is_instructor()} (should be True)"
        )
        
        self.log_test_result(
            "Admin Role - Create Courses",
            admin_create_courses,
            f"Admin can_create_courses(): {admin.can_create_courses()} (should be True)"
        )
        
        self.log_test_result(
            "Admin Role - Manage Users",
            admin_manage_users,
            f"Admin can_manage_users(): {admin.can_manage_users()} (should be True)"
        )
        
        if not all([admin_admin_check, admin_instructor_check, admin_create_courses, admin_manage_users]):
            all_passed = False
        
        return all_passed
    
    def test_status_based_access(self) -> bool:
        """Test that user status affects access control"""
        all_passed = True
        
        # Test inactive admin (should lose access)
        inactive_admin = User(
            email="inactive_admin@test.com",
            username="inactive_admin",
            full_name="Inactive Admin",
            role=UserRole.ADMIN,
            status=UserStatus.INACTIVE
        )
        
        # Inactive admin should not be able to manage users or create courses
        inactive_admin_manage = not inactive_admin.can_manage_users()
        inactive_admin_create = not inactive_admin.can_create_courses()
        
        self.log_test_result(
            "Inactive Admin - Manage Users",
            inactive_admin_manage,
            f"Inactive admin can_manage_users(): {inactive_admin.can_manage_users()} (should be False)"
        )
        
        self.log_test_result(
            "Inactive Admin - Create Courses",
            inactive_admin_create,
            f"Inactive admin can_create_courses(): {inactive_admin.can_create_courses()} (should be False)"
        )
        
        if not all([inactive_admin_manage, inactive_admin_create]):
            all_passed = False
        
        # Test suspended instructor (should lose access)
        suspended_instructor = User(
            email="suspended@test.com",
            username="suspended",
            full_name="Suspended Instructor",
            role=UserRole.INSTRUCTOR,
            status=UserStatus.SUSPENDED
        )
        
        suspended_create = not suspended_instructor.can_create_courses()
        
        self.log_test_result(
            "Suspended Instructor - Create Courses",
            suspended_create,
            f"Suspended instructor can_create_courses(): {suspended_instructor.can_create_courses()} (should be False)"
        )
        
        if not suspended_create:
            all_passed = False
        
        return all_passed
    
    def test_role_transitions(self) -> bool:
        """Test role change functionality"""
        all_passed = True
        
        # Create user as student
        user = User(
            email="test@test.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        
        # Initially student
        initial_student = not user.is_instructor() and not user.is_admin()
        
        self.log_test_result(
            "Initial Role - Student",
            initial_student,
            f"User starts as student: admin={user.is_admin()}, instructor={user.is_instructor()}"
        )
        
        # Promote to instructor
        user.change_role(UserRole.INSTRUCTOR)
        promoted_instructor = user.is_instructor() and not user.is_admin()
        
        self.log_test_result(
            "Role Change - Student to Instructor",
            promoted_instructor,
            f"After promotion: admin={user.is_admin()}, instructor={user.is_instructor()}"
        )
        
        # Promote to admin
        user.change_role(UserRole.ADMIN)
        promoted_admin = user.is_admin() and user.is_instructor()
        
        self.log_test_result(
            "Role Change - Instructor to Admin",
            promoted_admin,
            f"After admin promotion: admin={user.is_admin()}, instructor={user.is_instructor()}"
        )
        
        # Demote back to student
        user.change_role(UserRole.STUDENT)
        demoted_student = not user.is_instructor() and not user.is_admin()
        
        self.log_test_result(
            "Role Change - Admin to Student",
            demoted_student,
            f"After demotion: admin={user.is_admin()}, instructor={user.is_instructor()}"
        )
        
        if not all([initial_student, promoted_instructor, promoted_admin, demoted_student]):
            all_passed = False
        
        return all_passed
    
    def check_route_implementation(self) -> bool:
        """Check that route handlers properly implement role checking"""
        all_passed = True
        
        # Check user management routes file for proper role checking
        routes_file = project_root / 'services/user-management/routes.py'
        
        if routes_file.exists():
            with open(routes_file, 'r') as f:
                routes_content = f.read()
            
            # Look for admin role checks in routes
            admin_checks = [
                'current_user.is_admin()',
                'if not current_user.is_admin():',
                'raise HTTPException(status_code=403'
            ]
            
            admin_checks_found = all(check in routes_content for check in admin_checks)
            
            self.log_test_result(
                "Route Implementation - Admin Checks",
                admin_checks_found,
                f"Admin role checks found in routes: {admin_checks_found}"
            )
            
            if not admin_checks_found:
                all_passed = False
        else:
            self.log_test_result(
                "Route Implementation - File Check",
                False,
                "Routes file not found"
            )
            all_passed = False
        
        return all_passed
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all RBAC validation tests"""
        print("🔐 RBAC Validation Tests - Course Creator Platform")
        print("=" * 60)
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': []
        }
        
        # Run all test categories
        test_results = [
            self.test_user_role_methods(),
            self.test_status_based_access(),
            self.test_role_transitions(),
            self.check_route_implementation()
        ]
        
        # Calculate summary
        for test_result in self.results:
            results['total_tests'] += 1
            if test_result['passed']:
                results['passed_tests'] += 1
            else:
                results['failed_tests'] += 1
        
        results['test_results'] = self.results
        results['overall_success'] = all(test_results)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 RBAC VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Overall Success: {results['overall_success']}")
        
        return results


def main():
    """Main validation entry point"""
    validator = RBACValidationTest()
    results = validator.run_all_tests()
    
    # Save results
    report_file = project_root / 'rbac_validation_report.json'
    import json
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return exit code
    return 0 if results['overall_success'] else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)