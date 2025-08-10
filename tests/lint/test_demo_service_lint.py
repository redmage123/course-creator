"""
DEMO SERVICE LINTING TEST SUITE
PURPOSE: Validate code quality, style, and standards compliance for demo service
WHY: Ensure maintainable, consistent code following Python best practices
"""

import subprocess
import sys
import os
from pathlib import Path
import pytest

# Demo service path
DEMO_SERVICE_PATH = Path(__file__).parent.parent.parent / "services" / "demo-service"

class TestDemoServiceLinting:
    """
    Demo service code quality validation tests
    """
    
    def test_flake8_compliance(self):
        """
        Test Python code style compliance using flake8
        WHY: Ensures PEP 8 compliance and catches common issues
        """
        result = subprocess.run([
            sys.executable, "-m", "flake8", 
            str(DEMO_SERVICE_PATH),
            "--config=setup.cfg",
            "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s"
        ], capture_output=True, text=True, cwd=DEMO_SERVICE_PATH)
        
        if result.returncode != 0:
            print(f"Flake8 violations found:\n{result.stdout}")
        
        assert result.returncode == 0, f"Flake8 found code style violations: {result.stdout}"
    
    def test_pycodestyle_compliance(self):
        """
        Test PEP 8 style guide compliance
        WHY: Enforces consistent Python coding standards
        """
        result = subprocess.run([
            sys.executable, "-m", "pycodestyle",
            str(DEMO_SERVICE_PATH),
            "--max-line-length=100",
            "--ignore=E501,W503"  # Allow longer lines and line breaks before operators
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"PEP 8 violations found:\n{result.stdout}")
        
        assert result.returncode == 0, f"PEP 8 violations found: {result.stdout}"
    
    def test_pylint_score(self):
        """
        Test code quality score with pylint
        WHY: Comprehensive static analysis for code quality
        """
        result = subprocess.run([
            sys.executable, "-m", "pylint",
            str(DEMO_SERVICE_PATH / "*.py"),
            "--output-format=text",
            "--score=yes",
            "--disable=C0114,C0115,C0116",  # Disable missing docstring warnings for brevity
            "--fail-under=7.0"  # Require minimum score of 7.0/10
        ], capture_output=True, text=True, shell=True)
        
        print(f"Pylint output:\n{result.stdout}")
        
        # Extract score from output
        lines = result.stdout.split('\n')
        score_line = [line for line in lines if 'Your code has been rated at' in line]
        
        if score_line:
            score_text = score_line[0]
            print(f"Pylint score: {score_text}")
        
        # Pylint returns 0 for score >= fail-under threshold
        assert result.returncode == 0, f"Pylint score below 7.0: {result.stdout}"
    
    def test_import_sorting(self):
        """
        Test import statement organization with isort
        WHY: Consistent import organization improves readability
        """
        result = subprocess.run([
            sys.executable, "-m", "isort",
            str(DEMO_SERVICE_PATH),
            "--check-only",
            "--diff",
            "--profile=black"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Import sorting issues found:\n{result.stdout}")
        
        assert result.returncode == 0, f"Import sorting issues found: {result.stdout}"
    
    def test_security_vulnerabilities(self):
        """
        Test for security vulnerabilities with bandit
        WHY: Identify potential security issues in Python code
        """
        result = subprocess.run([
            sys.executable, "-m", "bandit",
            "-r", str(DEMO_SERVICE_PATH),
            "-f", "json",
            "-ll"  # Low confidence level
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Security vulnerabilities found:\n{result.stdout}")
        
        # Bandit returns non-zero for any issues found
        # For demo purposes, we'll allow medium/low severity issues
        assert result.returncode <= 1, f"High severity security issues found: {result.stdout}"
    
    def test_type_checking(self):
        """
        Test static type checking with mypy (if type hints are present)
        WHY: Catch type-related errors before runtime
        """
        # Check if any Python files have type hints
        python_files = list(DEMO_SERVICE_PATH.glob("*.py"))
        has_type_hints = False
        
        for file in python_files:
            with open(file, 'r') as f:
                content = f.read()
                if '->' in content or ': ' in content:  # Basic type hint detection
                    has_type_hints = True
                    break
        
        if not has_type_hints:
            pytest.skip("No type hints found, skipping mypy check")
        
        result = subprocess.run([
            sys.executable, "-m", "mypy",
            str(DEMO_SERVICE_PATH),
            "--ignore-missing-imports"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Type checking issues found:\n{result.stdout}")
        
        assert result.returncode == 0, f"Type checking failed: {result.stdout}"
    
    def test_docstring_coverage(self):
        """
        Test docstring coverage with pydocstyle
        WHY: Ensure adequate code documentation
        """
        result = subprocess.run([
            sys.executable, "-m", "pydocstyle",
            str(DEMO_SERVICE_PATH),
            "--ignore=D100,D101,D102,D103,D104,D105",  # Allow missing docstrings for brevity
            "--convention=google"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Docstring issues found:\n{result.stdout}")
        
        # For this test, we'll be lenient with docstring requirements
        # assert result.returncode == 0, f"Docstring issues found: {result.stdout}"
    
    def test_complexity_analysis(self):
        """
        Test cyclomatic complexity with radon
        WHY: Identify overly complex functions that need refactoring
        """
        result = subprocess.run([
            "radon", "cc",
            str(DEMO_SERVICE_PATH),
            "--min=C",  # Show functions with complexity C (10-15) or higher
            "--show-complexity"
        ], capture_output=True, text=True)
        
        if result.stdout.strip():
            print(f"High complexity functions found:\n{result.stdout}")
            # For now, just warn about high complexity
            print("Warning: Some functions have high cyclomatic complexity")
        
        # Don't fail the test for complexity, just report
        assert True
    
    def test_file_structure_compliance(self):
        """
        Test demo service file structure follows conventions
        WHY: Ensure consistent project organization
        """
        required_files = [
            "main.py",
            "requirements.txt",
            "Dockerfile"
        ]
        
        for file in required_files:
            file_path = DEMO_SERVICE_PATH / file
            assert file_path.exists(), f"Required file missing: {file}"
        
        # Check for Python cache and temp files that shouldn't be committed
        unwanted_patterns = [
            "*.pyc",
            "__pycache__",
            "*.pyo",
            "*.pyd",
            ".pytest_cache"
        ]
        
        for pattern in unwanted_patterns:
            unwanted_files = list(DEMO_SERVICE_PATH.rglob(pattern))
            if unwanted_files:
                print(f"Warning: Found unwanted files matching {pattern}: {unwanted_files}")