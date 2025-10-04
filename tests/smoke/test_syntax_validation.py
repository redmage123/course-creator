"""
Syntax Validation Smoke Tests

BUSINESS CONTEXT:
Before running any tests, we must ensure all Python files are syntactically valid.
Syntax errors prevent imports and mask other issues.

TECHNICAL IMPLEMENTATION:
- Validates all .py files can be compiled
- Runs before any other tests
- Fails fast on syntax errors

TEST COVERAGE:
- All Python files in services/
- All Python files in shared/
- All test files
"""

import pytest
import py_compile
import os
from pathlib import Path
from typing import List


def get_all_python_files() -> List[Path]:
    """
    Get all Python files in the project

    Returns:
        List of Path objects for all .py files
    """
    project_root = Path(__file__).parent.parent.parent
    python_files = []

    # Services
    services_dir = project_root / "services"
    if services_dir.exists():
        python_files.extend(services_dir.rglob("*.py"))

    # Shared
    shared_dir = project_root / "shared"
    if shared_dir.exists():
        python_files.extend(shared_dir.rglob("*.py"))

    # Tests
    tests_dir = project_root / "tests"
    if tests_dir.exists():
        python_files.extend(tests_dir.rglob("*.py"))

    # Exclude virtual environment and cache files
    python_files = [
        f for f in python_files
        if '.venv' not in str(f) and '__pycache__' not in str(f)
    ]

    return python_files


class TestSyntaxValidation:
    """
    Syntax validation tests that must pass before any other tests run

    CRITICAL REQUIREMENT:
    These tests MUST be run first. If any fail, all other tests are invalid.
    """

    @pytest.mark.order(1)
    def test_all_python_files_have_valid_syntax(self):
        """
        Validate that all Python files have valid syntax

        VALIDATION:
        - Every .py file can be compiled
        - No SyntaxError exceptions
        - Reports all syntax errors found
        """
        python_files = get_all_python_files()

        assert len(python_files) > 0, "No Python files found to validate"

        syntax_errors = []

        for py_file in python_files:
            try:
                py_compile.compile(str(py_file), doraise=True)
            except SyntaxError as e:
                syntax_errors.append({
                    'file': str(py_file),
                    'line': e.lineno,
                    'error': str(e.msg),
                    'text': e.text
                })

        if syntax_errors:
            error_msg = "\n\nSyntax Errors Found:\n"
            for err in syntax_errors:
                error_msg += f"\n  File: {err['file']}"
                error_msg += f"\n  Line {err['line']}: {err['error']}"
                if err['text']:
                    error_msg += f"\n  Code: {err['text'].strip()}"
                error_msg += "\n"

            pytest.fail(error_msg)

    @pytest.mark.order(1)
    def test_service_main_files_exist(self):
        """
        Verify all services have a main.py file

        VALIDATION:
        - Each service has a main.py entry point
        - Main files are syntactically valid
        """
        project_root = Path(__file__).parent.parent.parent
        services_dir = project_root / "services"

        services = [d for d in services_dir.iterdir() if d.is_dir() and '-' in d.name]

        missing_main = []

        for service in services:
            main_file = service / "main.py"
            if not main_file.exists():
                missing_main.append(str(service.name))

        assert not missing_main, f"Services missing main.py: {', '.join(missing_main)}"
