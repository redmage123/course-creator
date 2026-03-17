"""
Import Validation Smoke Tests

BUSINESS CONTEXT:
After syntax validation, we must verify all critical modules can be imported.
Import errors prevent tests from running and mask other issues.

TECHNICAL IMPLEMENTATION:
- Attempts to import key modules from each service
- Validates dependency resolution
- Reports import errors with full traceback

TEST COVERAGE:
- Service main modules
- API routers
- Core domain entities
- Shared utilities
"""

import pytest
import sys
import importlib
from pathlib import Path
from typing import List, Tuple, Dict
import traceback


class TestImportValidation:
    """
    Import validation tests that run after syntax validation

    CRITICAL REQUIREMENT:
    These tests validate that modules can be imported without errors.
    Must run before unit tests.
    """

    @pytest.mark.order(2)
    def test_user_management_imports(self):
        """Test user-management service imports"""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        import_tests = [
            ('services.user_management.services.user_service', 'UserService'),
            ('services.user_management.services.auth_service', 'AuthService'),
            ('services.user_management.services.admin_service', 'AdminService'),
        ]

        self._validate_imports(import_tests, "user-management")

    @pytest.mark.order(2)
    def test_organization_management_imports(self):
        """Test organization-management service imports"""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        import_tests = [
            ('services.organization_management.api.rbac_endpoints', 'router'),
            ('services.organization_management.application.services.membership_service', 'MembershipService'),
            ('services.organization_management.domain.entities.organization', 'Organization'),
        ]

        self._validate_imports(import_tests, "organization-management")

    @pytest.mark.order(2)
    def test_course_management_imports(self):
        """Test course-management service imports"""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        import_tests = [
            ('services.course_management.models.course', 'Course'),
            ('services.course_management.models.course_video', 'CourseVideo'),
        ]

        self._validate_imports(import_tests, "course-management")

    @pytest.mark.order(2)
    def test_content_management_imports(self):
        """Test content-management service imports"""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        import_tests = [
            ('services.content_management.domain.entities.quiz', 'Quiz'),
            ('services.content_management.domain.entities.feedback', 'Feedback'),
        ]

        self._validate_imports(import_tests, "content-management")

    @pytest.mark.order(2)
    def test_lab_manager_imports(self):
        """Test lab-manager service imports"""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        import_tests = [
            ('services.lab_manager.domain.entities.lab_environment', 'LabEnvironment'),
        ]

        self._validate_imports(import_tests, "lab-manager")

    @pytest.mark.order(2)
    def test_rag_service_imports(self):
        """Test rag-service imports"""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        import_tests = [
            ('services.rag_service.models.rag_models', 'RAGRequest'),
        ]

        self._validate_imports(import_tests, "rag-service")

    @pytest.mark.order(2)
    def test_demo_service_imports(self):
        """Test demo-service imports"""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        import_tests = [
            ('services.demo_service.services.data_generator', 'DataGenerator'),
        ]

        self._validate_imports(import_tests, "demo-service")

    @pytest.mark.order(2)
    def test_shared_utilities_imports(self):
        """Test shared utilities can be imported"""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        import_tests = [
            ('shared.exceptions.base_exceptions', 'BaseServiceException'),
            ('shared.cache.redis_cache', 'RedisCache'),
        ]

        self._validate_imports(import_tests, "shared")

    def _validate_imports(self, import_tests: List[Tuple[str, str]], service_name: str):
        """
        Validate a list of imports

        Args:
            import_tests: List of (module_path, class_name) tuples
            service_name: Name of service for error reporting
        """
        import_errors = []

        for module_path, class_name in import_tests:
            try:
                module = importlib.import_module(module_path)
                if class_name and not hasattr(module, class_name):
                    import_errors.append({
                        'module': module_path,
                        'class': class_name,
                        'error': f"Module has no attribute '{class_name}'"
                    })
            except ImportError as e:
                import_errors.append({
                    'module': module_path,
                    'class': class_name,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
            except Exception as e:
                import_errors.append({
                    'module': module_path,
                    'class': class_name,
                    'error': f"Unexpected error: {str(e)}",
                    'traceback': traceback.format_exc()
                })

        if import_errors:
            error_msg = f"\n\nImport Errors in {service_name}:\n"
            for err in import_errors:
                error_msg += f"\n  Module: {err['module']}"
                if err.get('class'):
                    error_msg += f"\n  Class: {err['class']}"
                error_msg += f"\n  Error: {err['error']}"
                if err.get('traceback'):
                    error_msg += f"\n  Traceback:\n{err['traceback']}"
                error_msg += "\n"

            pytest.fail(error_msg)
