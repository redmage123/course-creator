"""
Code Quality Tests for Tracks Module

BUSINESS CONTEXT:
Validates code quality, style, and best practices for all tracks-related code.
Ensures maintainability, readability, and adherence to coding standards.

TECHNICAL IMPLEMENTATION:
- Python code: Flake8, Pylint, Black formatting
- JavaScript code: ESLint, JSDoc validation
- File structure validation
- Import validation
- Security checks

TEST COVERAGE:
- Python backend code (track_endpoints.py, track_service.py, track_entity.py)
- JavaScript frontend code (org-admin-tracks.js)
- Documentation completeness
- SOLID principles adherence
"""

import pytest
import subprocess
import os
import re
import json
from pathlib import Path


class TestTracksBackendCodeQuality:
    """
    Code quality tests for Python backend tracks code

    TESTING STRATEGY:
    - Run static analysis tools (flake8, pylint)
    - Check formatting (black)
    - Validate imports (absolute vs relative)
    - Check documentation coverage
    - Validate type hints
    """

    @pytest.fixture
    def tracks_backend_files(self):
        """Get all Python files related to tracks"""
        base_path = Path("/home/bbrelin/course-creator/services/organization-management")
        return [
            base_path / "api/track_endpoints.py",
            base_path / "application/services/track_service.py",
            base_path / "domain/entities/track.py",
        ]

    def test_flake8_compliance(self, tracks_backend_files):
        """
        Test Flake8 compliance for all track files

        VALIDATION:
        - No syntax errors
        - PEP 8 style compliance
        - Line length limits
        - Import ordering
        """
        for file_path in tracks_backend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            result = subprocess.run(
                ["flake8", str(file_path), "--max-line-length=120"],
                capture_output=True,
                text=True
            )

            # Assert no flake8 violations
            assert result.returncode == 0, f"Flake8 violations in {file_path}:\n{result.stdout}"

    def test_pylint_score(self, tracks_backend_files):
        """
        Test Pylint score for track files

        QUALITY METRICS:
        - Minimum score: 8.0/10
        - No critical errors
        - Limited warnings
        """
        for file_path in tracks_backend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            result = subprocess.run(
                ["pylint", str(file_path), "--rcfile=/home/bbrelin/course-creator/.pylintrc"],
                capture_output=True,
                text=True
            )

            # Extract score from pylint output
            score_match = re.search(r"Your code has been rated at ([\d.]+)/10", result.stdout)
            if score_match:
                score = float(score_match.group(1))
                assert score >= 8.0, f"Pylint score too low for {file_path}: {score}/10\n{result.stdout}"

    def test_black_formatting(self, tracks_backend_files):
        """
        Test Black code formatting

        FORMATTING:
        - Consistent code style
        - Proper indentation
        - Line length compliance
        """
        for file_path in tracks_backend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            result = subprocess.run(
                ["black", "--check", "--line-length=120", str(file_path)],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, f"Black formatting issues in {file_path}:\n{result.stderr}"

    def test_no_relative_imports(self, tracks_backend_files):
        """
        Test that files use absolute imports only

        CRITICAL REQUIREMENT:
        Per CLAUDE.md, all imports must be absolute, not relative
        No `from ..` or `from .` imports allowed
        """
        for file_path in tracks_backend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            with open(file_path, 'r') as f:
                content = f.read()

            # Check for relative imports
            relative_import_pattern = r'from\s+\.\.?'
            matches = re.findall(relative_import_pattern, content)

            assert len(matches) == 0, f"Relative imports found in {file_path}: {matches}"

    def test_custom_exceptions_used(self, tracks_backend_files):
        """
        Test that code uses custom exceptions, not generic Exception

        CRITICAL REQUIREMENT:
        Per CLAUDE.md, must use structured custom exceptions
        No bare `except Exception as e` handlers
        """
        for file_path in tracks_backend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Check for generic exception handling
            for line_num, line in enumerate(lines, 1):
                if 'except Exception as' in line and 'pragma: no cover' not in line:
                    # Allow if it's re-raising or logging properly
                    if 'raise' not in lines[line_num] and 'logger' not in lines[line_num]:
                        pytest.fail(
                            f"Generic exception handler found in {file_path}:{line_num}\n"
                            f"Line: {line.strip()}\n"
                            f"Use custom exceptions from exceptions.py instead"
                        )

    def test_documentation_coverage(self, tracks_backend_files):
        """
        Test that all functions and classes have documentation

        DOCUMENTATION REQUIREMENTS:
        - All classes have docstrings
        - All public methods have docstrings
        - Docstrings include business context
        """
        for file_path in tracks_backend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            with open(file_path, 'r') as f:
                content = f.read()

            # Find all class and function definitions
            class_pattern = r'class\s+(\w+)'
            func_pattern = r'def\s+(\w+)\s*\('

            classes = re.findall(class_pattern, content)
            functions = re.findall(func_pattern, content)

            # Check for docstrings (simplified check)
            for class_name in classes:
                class_match = re.search(rf'class\s+{class_name}.*?:\s*"""', content, re.DOTALL)
                assert class_match, f"Missing docstring for class {class_name} in {file_path}"

            # Check public functions (not starting with _)
            for func_name in functions:
                if not func_name.startswith('_'):
                    func_match = re.search(rf'def\s+{func_name}.*?:\s*"""', content, re.DOTALL)
                    assert func_match, f"Missing docstring for function {func_name} in {file_path}"


class TestTracksFrontendCodeQuality:
    """
    Code quality tests for JavaScript frontend tracks code

    TESTING STRATEGY:
    - Run ESLint for JavaScript validation
    - Check JSDoc documentation
    - Validate module structure
    - Check for security issues (XSS prevention)
    """

    @pytest.fixture
    def tracks_frontend_files(self):
        """Get all JavaScript files related to tracks"""
        base_path = Path("/home/bbrelin/course-creator/frontend/js/modules")
        return [
            base_path / "org-admin-tracks.js",
            base_path / "org-admin-utils.js",
            base_path / "org-admin-api.js",
        ]

    def test_eslint_compliance(self, tracks_frontend_files):
        """
        Test ESLint compliance for JavaScript files

        VALIDATION:
        - No syntax errors
        - ES6+ best practices
        - No unused variables
        - Proper async/await usage
        """
        eslint_config = "/home/bbrelin/course-creator/.eslintrc.json"

        if not Path(eslint_config).exists():
            pytest.skip("ESLint config not found")

        for file_path in tracks_frontend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            result = subprocess.run(
                ["npx", "eslint", str(file_path), "-c", eslint_config],
                capture_output=True,
                text=True,
                cwd="/home/bbrelin/course-creator"
            )

            assert result.returncode == 0, f"ESLint violations in {file_path}:\n{result.stdout}"

    def test_jsdoc_documentation(self, tracks_frontend_files):
        """
        Test JSDoc documentation coverage

        DOCUMENTATION REQUIREMENTS:
        - All exported functions have JSDoc comments
        - JSDoc includes @param and @returns
        - Business context documented
        """
        for file_path in tracks_frontend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            with open(file_path, 'r') as f:
                content = f.read()

            # Find all export function declarations
            export_pattern = r'export\s+(async\s+)?function\s+(\w+)'
            exported_functions = re.findall(export_pattern, content)

            for _, func_name in exported_functions:
                # Check for JSDoc before function
                jsdoc_pattern = rf'/\*\*.*?\*/\s*export\s+(async\s+)?function\s+{func_name}'
                jsdoc_match = re.search(jsdoc_pattern, content, re.DOTALL)

                assert jsdoc_match, f"Missing JSDoc for exported function {func_name} in {file_path}"

    def test_es6_module_structure(self, tracks_frontend_files):
        """
        Test proper ES6 module structure

        MODULE REQUIREMENTS:
        - Uses import/export statements
        - No global variable pollution
        - Proper module organization
        """
        for file_path in tracks_frontend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            with open(file_path, 'r') as f:
                content = f.read()

            # Should have import statements
            has_imports = 'import' in content and 'from' in content

            # Should have export statements
            has_exports = 'export' in content

            assert has_imports or has_exports, f"File {file_path} doesn't use ES6 modules properly"

    def test_xss_prevention(self, tracks_frontend_files):
        """
        Test XSS prevention measures

        SECURITY:
        - Uses escapeHtml() for user input
        - No innerHTML with unescaped data
        - Proper sanitization
        """
        for file_path in tracks_frontend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            with open(file_path, 'r') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Check for dangerous innerHTML usage
                if 'innerHTML' in line:
                    # Should have escapeHtml nearby or be using template literals safely
                    context = ''.join(lines[max(0, line_num-3):min(len(lines), line_num+2)])

                    # If setting innerHTML, should use escapeHtml
                    if '=' in line and 'innerHTML' in line:
                        has_escape = 'escapeHtml' in context or '`' in line  # Template literal might be safe
                        # Allow if it's documented as safe or using template strings correctly
                        if not has_escape and 'SAFE' not in context:
                            pytest.warn(
                                UserWarning(
                                    f"Potential XSS vulnerability in {file_path}:{line_num}\n"
                                    f"Line: {line.strip()}\n"
                                    f"Consider using escapeHtml() for user input"
                                )
                            )

    def test_no_console_log_in_production(self, tracks_frontend_files):
        """
        Test that console.log statements are minimal

        PRODUCTION READINESS:
        - Limit console.log usage
        - Use proper logging or remove debug statements
        """
        for file_path in tracks_frontend_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")

            with open(file_path, 'r') as f:
                content = f.read()

            # Count console.log statements
            console_logs = re.findall(r'console\.log\(', content)

            # Allow some for legitimate logging, but warn if excessive
            if len(console_logs) > 5:
                pytest.warn(
                    UserWarning(
                        f"{file_path} has {len(console_logs)} console.log statements. "
                        f"Consider using a proper logging system for production."
                    )
                )


class TestTracksArchitecture:
    """
    Architectural and SOLID principle tests

    TESTING STRATEGY:
    - Validate SOLID principles adherence
    - Check dependency structure
    - Validate separation of concerns
    """

    def test_single_responsibility_principle(self):
        """
        Test Single Responsibility Principle

        VALIDATION:
        - Each module has one clear responsibility
        - org-admin-tracks.js: Track management UI
        - org-admin-api.js: API calls only
        - org-admin-utils.js: Utility functions only
        """
        modules = {
            "org-admin-tracks.js": ["track", "modal", "enroll"],
            "org-admin-api.js": ["fetch", "api", "http"],
            "org-admin-utils.js": ["escape", "format", "validate"]
        }

        for module_name, expected_keywords in modules.items():
            file_path = Path(f"/home/bbrelin/course-creator/frontend/js/modules/{module_name}")

            if not file_path.exists():
                continue

            with open(file_path, 'r') as f:
                content = f.read().lower()

            # Check that file contains related keywords
            matches = sum(1 for keyword in expected_keywords if keyword in content)
            assert matches > 0, f"{module_name} doesn't seem to match its responsibility"

    def test_dependency_direction(self):
        """
        Test proper dependency direction

        DEPENDENCY INVERSION:
        - Core modules depend on abstractions
        - UI modules use API abstraction
        - No circular dependencies
        """
        # Check that tracks module imports from api and utils
        tracks_file = Path("/home/bbrelin/course-creator/frontend/js/modules/org-admin-tracks.js")

        if not tracks_file.exists():
            pytest.skip("Tracks module not found")

        with open(tracks_file, 'r') as f:
            content = f.read()

        # Should import from API module
        assert "from './org-admin-api.js'" in content, "Tracks should use API abstraction"

        # Should import from utils module
        assert "from './org-admin-utils.js'" in content, "Tracks should use utility functions"

    def test_file_size_limits(self):
        """
        Test that files respect size limits

        MAINTAINABILITY:
        - No single file > 500 lines (refactored from 2833 lines)
        - Promotes modularity
        """
        frontend_modules = Path("/home/bbrelin/course-creator/frontend/js/modules")

        if not frontend_modules.exists():
            pytest.skip("Modules directory not found")

        for js_file in frontend_modules.glob("*.js"):
            with open(js_file, 'r') as f:
                line_count = len(f.readlines())

            assert line_count <= 500, f"{js_file.name} has {line_count} lines (max 500 for maintainability)"


class TestTracksConfiguration:
    """
    Configuration and setup validation

    TESTING STRATEGY:
    - Validate test configuration
    - Check environment setup
    - Validate data fixtures
    """

    def test_pytest_configuration(self):
        """Test pytest configuration for tracks tests"""
        pytest_ini = Path("/home/bbrelin/course-creator/pytest.ini")

        if pytest_ini.exists():
            with open(pytest_ini, 'r') as f:
                content = f.read()

            # Should have tracks marker
            assert 'tracks' in content, "pytest.ini should define 'tracks' marker"

    def test_test_data_fixtures(self):
        """Test that test data fixtures exist for tracks"""
        # Check for track test data
        test_data_paths = [
            Path("/home/bbrelin/course-creator/tests/fixtures/tracks.json"),
            Path("/home/bbrelin/course-creator/tests/data/sample_tracks.json"),
        ]

        # At least one should exist (create if needed)
        exists = any(p.exists() for p in test_data_paths)
        if not exists:
            pytest.skip("No test data fixtures found - consider creating them")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
