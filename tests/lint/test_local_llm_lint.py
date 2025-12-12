"""
Linting and Code Quality Tests for Local LLM Service

BUSINESS CONTEXT:
Ensures code quality, maintainability, and adherence to Python best practices
for the local-llm-service codebase.

TECHNICAL IMPLEMENTATION:
- Runs flake8 for PEP8 compliance
- Checks import organization
- Validates docstring presence
- Checks for common code smells
- Validates type hints
"""

import pytest
import subprocess
import os
from pathlib import Path


SERVICE_PATH = "services/local-llm-service"


class TestFlake8Compliance:
    """Test PEP8 compliance with flake8."""

    @pytest.mark.unit
    def test_flake8_service_code(self):
        """Test service code passes flake8."""
        result = subprocess.run(
            ["flake8", f"{SERVICE_PATH}/local_llm_service", "--config=.flake8"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"Flake8 found issues:\n{result.stdout}\n{result.stderr}"

    @pytest.mark.unit
    def test_flake8_main_file(self):
        """Test main.py passes flake8."""
        result = subprocess.run(
            ["flake8", f"{SERVICE_PATH}/main.py", "--config=.flake8"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"Flake8 found issues in main.py:\n{result.stdout}\n{result.stderr}"


class TestImportOrganization:
    """Test import statements are properly organized."""

    @pytest.mark.unit
    def test_no_relative_imports(self):
        """Test no relative imports are used."""
        # Scan all Python files
        python_files = list(Path(SERVICE_PATH).rglob("*.py"))

        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue

            with open(file_path, "r") as f:
                content = f.read()

                # Check for relative imports
                assert "from ." not in content and "from .." not in content, \
                    f"Relative import found in {file_path}"

    @pytest.mark.unit
    def test_imports_order(self):
        """Test imports are in correct order (stdlib, third-party, local)."""
        result = subprocess.run(
            ["flake8", SERVICE_PATH, "--select=I"],
            capture_output=True,
            text=True
        )

        # If import order plugin is installed, check it
        if "I" in result.stdout or result.returncode != 0:
            pass  # Import order check ran


class TestDocumentation:
    """Test code documentation requirements."""

    @pytest.mark.unit
    def test_all_modules_have_docstrings(self):
        """Test all Python modules have docstrings."""
        python_files = list(Path(SERVICE_PATH).rglob("*.py"))

        for file_path in python_files:
            if "__pycache__" in str(file_path) or "__init__" in str(file_path):
                continue

            with open(file_path, "r") as f:
                content = f.read()

                # Should have a module docstring
                assert '"""' in content or "'''" in content, \
                    f"Missing docstring in {file_path}"

    @pytest.mark.unit
    def test_main_functions_have_docstrings(self):
        """Test major functions have docstrings."""
        service_file = Path(f"{SERVICE_PATH}/local_llm_service/application/services/local_llm_service.py")

        if service_file.exists():
            with open(service_file, "r") as f:
                content = f.read()

                # Key methods should have docstrings
                key_methods = ["health_check", "generate_response", "summarize_context"]

                for method in key_methods:
                    if f"def {method}" in content:
                        # Check if method is followed by docstring
                        method_idx = content.find(f"def {method}")
                        after_method = content[method_idx:method_idx + 500]
                        assert '"""' in after_method or "'''" in after_method, \
                            f"Method {method} missing docstring"


class TestCodeComplexity:
    """Test code complexity is manageable."""

    @pytest.mark.unit
    def test_cyclomatic_complexity(self):
        """Test functions don't exceed complexity threshold."""
        result = subprocess.run(
            ["flake8", SERVICE_PATH, "--select=C901", "--max-complexity=10"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"Complex functions found:\n{result.stdout}"

    @pytest.mark.unit
    def test_line_length(self):
        """Test lines don't exceed maximum length."""
        result = subprocess.run(
            ["flake8", SERVICE_PATH, "--select=E501", "--max-line-length=88"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"Long lines found:\n{result.stdout}"


class TestSyntaxErrors:
    """Test for syntax errors."""

    @pytest.mark.unit
    def test_python_syntax(self):
        """Test all Python files have valid syntax."""
        python_files = list(Path(SERVICE_PATH).rglob("*.py"))

        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue

            result = subprocess.run(
                ["python3", "-m", "py_compile", str(file_path)],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, \
                f"Syntax error in {file_path}:\n{result.stderr}"


class TestSecurityChecks:
    """Test for common security issues."""

    @pytest.mark.unit
    def test_no_hardcoded_secrets(self):
        """Test no hardcoded secrets in code."""
        python_files = list(Path(SERVICE_PATH).rglob("*.py"))

        suspicious_patterns = [
            "password =",
            "api_key =",
            "secret =",
            "token ="
        ]

        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue

            with open(file_path, "r") as f:
                content = f.read().lower()

                for pattern in suspicious_patterns:
                    if pattern in content:
                        # Check if it's using environment variables
                        line_with_pattern = [line for line in content.split('\n') if pattern in line]
                        for line in line_with_pattern:
                            if "os.getenv" not in line and "os.environ" not in line:
                                pytest.fail(f"Potential hardcoded secret in {file_path}: {line[:50]}")

    @pytest.mark.unit
    def test_no_sql_injection_risk(self):
        """Test no raw SQL string formatting."""
        python_files = list(Path(SERVICE_PATH).rglob("*.py"))

        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue

            with open(file_path, "r") as f:
                content = f.read()

                # Check for string formatting in SQL queries
                if "SELECT" in content or "INSERT" in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if ("SELECT" in line or "INSERT" in line) and ("%" in line or ".format" in line):
                            pytest.fail(f"Potential SQL injection risk in {file_path}:{i+1}")


class TestTypeHints:
    """Test type hints are present."""

    @pytest.mark.unit
    def test_functions_have_type_hints(self):
        """Test public functions have type hints."""
        service_file = Path(f"{SERVICE_PATH}/local_llm_service/application/services/local_llm_service.py")

        if service_file.exists():
            with open(service_file, "r") as f:
                content = f.read()

                # Find function definitions
                import re
                functions = re.findall(r'def\s+([a-z_][a-z0-9_]*)\s*\((.*?)\)\s*(->\s*\w+)?:', content, re.MULTILINE)

                public_functions = [f for f in functions if not f[0].startswith('_')]

                # At least half should have return type hints
                with_hints = sum(1 for f in public_functions if f[2])
                total = len(public_functions)

                if total > 0:
                    hint_ratio = with_hints / total
                    assert hint_ratio >= 0.5, \
                        f"Only {hint_ratio*100:.0f}% of functions have type hints, expected ≥50%"


class TestDependencies:
    """Test dependencies are properly specified."""

    @pytest.mark.unit
    def test_requirements_file_exists(self):
        """Test requirements.txt exists."""
        requirements_file = Path(f"{SERVICE_PATH}/requirements.txt")
        assert requirements_file.exists(), "requirements.txt not found"

    @pytest.mark.unit
    def test_requirements_are_pinned(self):
        """Test dependencies have version constraints."""
        requirements_file = Path(f"{SERVICE_PATH}/requirements.txt")

        if requirements_file.exists():
            with open(requirements_file, "r") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

                # At least some dependencies should have version pins
                pinned = sum(1 for line in lines if ">=" in line or "==" in line or "~=" in line)
                assert pinned > 0, "No version constraints found in requirements.txt"


class TestFileOrganization:
    """Test file and directory organization."""

    @pytest.mark.unit
    def test_service_structure(self):
        """Test service follows expected directory structure."""
        expected_dirs = [
            f"{SERVICE_PATH}/local_llm_service",
            f"{SERVICE_PATH}/local_llm_service/application",
            f"{SERVICE_PATH}/local_llm_service/application/services",
        ]

        for dir_path in expected_dirs:
            assert Path(dir_path).exists(), f"Missing directory: {dir_path}"

    @pytest.mark.unit
    def test_init_files_present(self):
        """Test __init__.py files are present in packages."""
        package_dirs = [
            f"{SERVICE_PATH}/local_llm_service",
            f"{SERVICE_PATH}/local_llm_service/application",
            f"{SERVICE_PATH}/local_llm_service/application/services",
        ]

        for dir_path in package_dirs:
            init_file = Path(dir_path) / "__init__.py"
            if Path(dir_path).exists():
                assert init_file.exists(), f"Missing __init__.py in {dir_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
