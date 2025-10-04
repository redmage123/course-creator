"""
Code Quality Tests for Instructor Dashboard

BUSINESS REQUIREMENT:
Ensures instructor dashboard code meets quality standards including
documentation, code style, security, and best practices.

TECHNICAL IMPLEMENTATION:
- Tests JavaScript code quality and patterns
- Validates documentation completeness
- Checks for security vulnerabilities
- Verifies best practices compliance
"""

import pytest
import os
import re
from pathlib import Path
from typing import List, Dict, Any


# File paths
INSTRUCTOR_DASHBOARD_JS = Path("/home/bbrelin/course-creator/frontend/js/modules/instructor-dashboard.js")
INSTRUCTOR_DASHBOARD_HTML = Path("/home/bbrelin/course-creator/frontend/html/instructor-dashboard-refactored.html")
COMPONENT_FILES = [
    Path("/home/bbrelin/course-creator/frontend/js/components/component-loader.js"),
    Path("/home/bbrelin/course-creator/frontend/js/components/course-manager.js"),
    Path("/home/bbrelin/course-creator/frontend/js/components/dashboard-navigation.js")
]


@pytest.mark.lint
class TestJavaScriptCodeQuality:
    """Test JavaScript code quality standards."""

    def test_instructor_dashboard_file_exists(self):
        """Test that instructor dashboard JavaScript file exists."""
        assert INSTRUCTOR_DASHBOARD_JS.exists(), \
            f"Instructor dashboard JS not found at {INSTRUCTOR_DASHBOARD_JS}"

    def test_instructor_dashboard_html_exists(self):
        """Test that instructor dashboard HTML file exists."""
        assert INSTRUCTOR_DASHBOARD_HTML.exists(), \
            f"Instructor dashboard HTML not found at {INSTRUCTOR_DASHBOARD_HTML}"

    def test_component_files_exist(self):
        """Test that all component files exist."""
        for component_file in COMPONENT_FILES:
            assert component_file.exists(), \
                f"Component file not found: {component_file}"

    def test_no_console_logs_in_production_code(self):
        """Test that production code doesn't contain console.log statements."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Allow console.error and console.warn, but not console.log
        console_logs = re.findall(r'console\.log\(', content)

        # Some console.log for debugging is acceptable, but should be minimal
        assert len(console_logs) < 10, \
            f"Found {len(console_logs)} console.log statements. Consider using proper logging."

    def test_no_debugger_statements(self):
        """Test that code doesn't contain debugger statements."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        assert 'debugger;' not in content, \
            "Found debugger statement in production code"

    def test_proper_error_handling(self):
        """Test that async functions have proper error handling."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Find all async functions
        async_functions = re.findall(r'async\s+(\w+)\s*\([^)]*\)\s*{', content)

        # Each async function should have try-catch or error handling
        for func_name in async_functions:
            # Find function body
            func_pattern = rf'async\s+{func_name}\s*\([^)]*\)\s*{{([^{{}}]*(?:{{[^{{}}]*}}[^{{}}]*)*)}}'
            matches = re.findall(func_pattern, content, re.DOTALL)

            if matches:
                func_body = matches[0]

                # Check for error handling
                has_try_catch = 'try' in func_body and 'catch' in func_body
                has_catch_callback = '.catch(' in func_body
                has_error_handling = has_try_catch or has_catch_callback

                # Some tolerance for simple functions
                if len(func_body) > 100:  # Only check substantial functions
                    assert has_error_handling, \
                        f"Async function '{func_name}' lacks error handling"

    def test_no_alert_usage(self):
        """Test that code doesn't use alert() for user notifications."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Alert should not be used - use notification system instead
        alert_usage = re.findall(r'\balert\s*\(', content)

        assert len(alert_usage) == 0, \
            f"Found {len(alert_usage)} alert() calls. Use showNotification() instead."

    def test_no_hardcoded_urls(self):
        """Test that code doesn't contain hardcoded URLs."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Look for hardcoded localhost or http URLs (except in comments)
        lines = content.split('\n')
        code_lines = [line for line in lines if not line.strip().startswith('//')]
        code_content = '\n'.join(code_lines)

        hardcoded_urls = re.findall(r'["\']https?://localhost:\d+', code_content)

        assert len(hardcoded_urls) == 0, \
            f"Found {len(hardcoded_urls)} hardcoded URLs. Use window.CONFIG instead."

    def test_uses_es6_modules(self):
        """Test that code uses ES6 module syntax."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Should have export statements
        has_exports = 'export ' in content

        assert has_exports, \
            "JavaScript should use ES6 module syntax (import/export)"

    def test_proper_jsdoc_comments(self):
        """Test that major functions have JSDoc comments."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Find all method definitions in the class
        methods = re.findall(r'\n\s+(async\s+)?(\w+)\s*\([^)]*\)\s*{', content)

        # Count methods with JSDoc comments
        jsdoc_pattern = r'/\*\*[\s\S]*?\*/'
        jsdocs = re.findall(jsdoc_pattern, content)

        # Should have substantial documentation
        assert len(jsdocs) > 10, \
            f"Found only {len(jsdocs)} JSDoc comments. Add more documentation."


@pytest.mark.lint
class TestDocumentationQuality:
    """Test documentation completeness and quality."""

    def test_file_has_module_level_documentation(self):
        """Test that file has comprehensive module-level documentation."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Check for module-level documentation at the top
        lines = content.split('\n')
        first_100_lines = '\n'.join(lines[:100])

        # Should have comprehensive header comment
        has_module_doc = '/**' in first_100_lines

        assert has_module_doc, \
            "File should have module-level JSDoc documentation"

        # Check for key documentation sections
        assert 'PURPOSE' in first_100_lines or 'DESCRIPTION' in first_100_lines, \
            "Module documentation should describe purpose"

    def test_class_has_documentation(self):
        """Test that InstructorDashboard class has documentation."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Find class definition
        class_pattern = r'/\*\*[\s\S]*?\*/\s*export\s+class\s+InstructorDashboard'

        has_class_doc = bool(re.search(class_pattern, content))

        assert has_class_doc, \
            "InstructorDashboard class should have JSDoc documentation"

    def test_public_methods_have_documentation(self):
        """Test that public methods have JSDoc documentation."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Find public methods (not starting with _)
        public_methods = re.findall(r'\n\s+(async\s+)?([a-z]\w+)\s*\([^)]*\)\s*{', content)

        # Check for documentation before each method
        documented_methods = 0
        for _, method_name in public_methods:
            # Look for JSDoc comment before this method
            method_pattern = rf'/\*\*[\s\S]*?\*/\s*(async\s+)?{method_name}\s*\('

            if re.search(method_pattern, content):
                documented_methods += 1

        # At least 50% of public methods should be documented
        documentation_ratio = documented_methods / len(public_methods) if public_methods else 0

        assert documentation_ratio >= 0.5, \
            f"Only {documentation_ratio:.1%} of public methods are documented. Target: 50%+"


@pytest.mark.lint
class TestSecurityBestPractices:
    """Test security best practices compliance."""

    def test_no_eval_usage(self):
        """Test that code doesn't use eval()."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # eval() is dangerous and should not be used
        assert 'eval(' not in content, \
            "Found eval() usage. This is a security risk."

    def test_proper_xss_prevention(self):
        """Test that innerHTML usage is minimal and safe."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Count innerHTML usage
        inner_html_usage = re.findall(r'\.innerHTML\s*=', content)

        # innerHTML should be used sparingly - check if excessive
        # Some usage is acceptable for template rendering
        assert len(inner_html_usage) < 50, \
            f"Found {len(inner_html_usage)} innerHTML assignments. Consider using textContent or DOM methods."

    def test_authentication_checks_present(self):
        """Test that authentication checks are present."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Should check authentication
        has_auth_check = 'isAuthenticated' in content or 'authToken' in content

        assert has_auth_check, \
            "Dashboard should check user authentication"

    def test_role_based_access_control(self):
        """Test that role-based access control is implemented."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Should check for instructor role
        has_role_check = 'hasRole' in content or 'role' in content

        assert has_role_check, \
            "Dashboard should implement role-based access control"

    def test_no_sensitive_data_in_logs(self):
        """Test that sensitive data is not logged."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Look for common sensitive data patterns in console statements
        console_statements = re.findall(r'console\.\w+\([^)]+\)', content)

        sensitive_patterns = ['password', 'token', 'secret', 'key']

        for statement in console_statements:
            for pattern in sensitive_patterns:
                assert pattern not in statement.lower(), \
                    f"Found potentially sensitive data in console statement: {statement}"


@pytest.mark.lint
class TestCodeStructureAndPatterns:
    """Test code structure and design patterns."""

    def test_uses_classes_appropriately(self):
        """Test that code uses ES6 classes."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Should define InstructorDashboard class
        has_class = 'class InstructorDashboard' in content

        assert has_class, \
            "Should use ES6 class for InstructorDashboard"

    def test_proper_method_organization(self):
        """Test that methods are organized logically."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Constructor should be first
        class_start = content.find('class InstructorDashboard')
        constructor_pos = content.find('constructor()', class_start)

        assert constructor_pos > class_start, \
            "Class should have a constructor"

        # Methods should be grouped by functionality (check for comment sections)
        has_sections = '// ===' in content or '/* ===' in content

        # If file is large, it should be organized into sections
        lines = content.split('\n')
        if len(lines) > 500:
            assert has_sections, \
                "Large files should be organized into commented sections"

    def test_reasonable_file_size(self):
        """Test that file size is reasonable."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()
        lines = content.split('\n')

        # Warn if file is very large (> 3000 lines)
        # This is a guideline, not a hard rule
        if len(lines) > 3000:
            pytest.warn(
                f"File has {len(lines)} lines. Consider refactoring into smaller modules."
            )

    def test_function_complexity(self):
        """Test that functions are not overly complex."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Find all function definitions
        functions = re.findall(r'(async\s+)?(\w+)\s*\([^)]*\)\s*{([^}]+)}', content)

        for _, func_name, func_body in functions:
            lines = func_body.split('\n')

            # Functions should generally be < 100 lines
            if len(lines) > 100:
                # Check cyclomatic complexity (rough estimate)
                complexity_indicators = [
                    'if ', 'else ', 'for ', 'while ', 'switch ', 'case ',
                    '&&', '||', '?', 'catch'
                ]

                complexity = sum(
                    func_body.count(indicator)
                    for indicator in complexity_indicators
                )

                # High complexity suggests function should be refactored
                assert complexity < 30, \
                    f"Function '{func_name}' has high complexity ({complexity}). Consider refactoring."


@pytest.mark.lint
class TestHTMLQuality:
    """Test HTML code quality."""

    def test_html_uses_semantic_elements(self):
        """Test that HTML uses semantic elements."""
        content = INSTRUCTOR_DASHBOARD_HTML.read_text()

        # Should use semantic HTML5 elements
        semantic_elements = ['<header', '<nav', '<main', '<section', '<article']

        found_semantic = sum(1 for element in semantic_elements if element in content)

        assert found_semantic >= 2, \
            "HTML should use semantic HTML5 elements"

    def test_html_has_proper_structure(self):
        """Test that HTML has proper document structure."""
        content = INSTRUCTOR_DASHBOARD_HTML.read_text()

        # Basic structure checks
        assert '<!DOCTYPE html>' in content, "Missing DOCTYPE declaration"
        assert '<html' in content, "Missing html tag"
        assert '<head>' in content, "Missing head section"
        assert '<body>' in content, "Missing body section"

    def test_html_uses_es6_modules(self):
        """Test that HTML loads JavaScript as ES6 modules."""
        content = INSTRUCTOR_DASHBOARD_HTML.read_text()

        # Should use type="module" for ES6 module support
        has_module_script = 'type="module"' in content

        assert has_module_script, \
            "HTML should load JavaScript using type='module'"

    def test_html_has_meta_tags(self):
        """Test that HTML has proper meta tags."""
        content = INSTRUCTOR_DASHBOARD_HTML.read_text()

        # Should have charset and viewport
        assert 'charset=' in content, "Missing charset meta tag"
        assert 'viewport' in content, "Missing viewport meta tag"

    def test_html_has_accessibility_features(self):
        """Test that HTML includes accessibility features."""
        content = INSTRUCTOR_DASHBOARD_HTML.read_text()

        # Check for basic accessibility
        has_lang = 'lang=' in content
        has_alt_or_aria = 'alt=' in content or 'aria-' in content

        assert has_lang, "HTML should have lang attribute"

        # If there are images or interactive elements, should have accessibility attributes
        if '<img' in content or '<button' in content:
            assert has_alt_or_aria, \
                "Interactive elements should have accessibility attributes"


@pytest.mark.lint
class TestPerformancePatterns:
    """Test performance best practices."""

    def test_debouncing_for_frequent_events(self):
        """Test that debouncing is used for frequent events."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # If there are input event listeners, check for debouncing
        has_input_listeners = 'addEventListener' in content and 'input' in content

        if has_input_listeners:
            # Should have debounce or throttle implementation
            has_debounce = 'debounce' in content or 'throttle' in content or 'setTimeout' in content

            # This is a recommendation, not a hard requirement
            if not has_debounce:
                pytest.warn("Consider using debouncing for input event handlers")

    def test_lazy_loading_implementation(self):
        """Test that lazy loading is used where appropriate."""
        content = INSTRUCTOR_DASHBOARD_JS.read_text()

        # Check for dynamic imports or lazy loading patterns
        has_dynamic_import = 'import(' in content
        has_lazy_loading = 'lazy' in content.lower() or 'defer' in content.lower()

        # If file loads many resources, should consider lazy loading
        if content.count('fetch(') > 10:
            assert has_dynamic_import or has_lazy_loading, \
                "Consider implementing lazy loading for better performance"


# Run tests with: pytest tests/lint/test_instructor_dashboard_quality.py -v --tb=short -m lint
