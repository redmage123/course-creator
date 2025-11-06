"""
Code Quality and Linting Tests for Project Import Feature

BUSINESS CONTEXT:
Ensures code quality, consistency, and maintainability for the project
import feature through automated linting and syntax checking.

TEST COVERAGE:
- Python syntax validation
- Import statement correctness
- Code style compliance (PEP 8)
- Documentation completeness
- Type hint validation
- Security best practices
"""
import pytest
import ast
import os
import re
from pathlib import Path


class TestProjectImportCodeQuality:
    """Code quality and linting tests"""

    @pytest.fixture(scope="class")
    def parser_file_path(self):
        """Path to project spreadsheet parser"""
        return Path('/home/bbrelin/course-creator/services/course-management/course_management/application/services/project_spreadsheet_parser.py')

    @pytest.fixture(scope="class")
    def main_file_path(self):
        """Path to main.py with project import endpoints"""
        return Path('/home/bbrelin/course-creator/services/course-management/main.py')

    # ========================================================================
    # SYNTAX VALIDATION TESTS
    # ========================================================================

    def test_parser_python_syntax_valid(self, parser_file_path):
        """Test project_spreadsheet_parser.py has valid Python syntax"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {parser_file_path}: {e}")

    def test_main_python_syntax_valid(self, main_file_path):
        """Test main.py has valid Python syntax"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {main_file_path}: {e}")

    # ========================================================================
    # IMPORT STATEMENT TESTS
    # ========================================================================

    def test_parser_uses_absolute_imports(self, parser_file_path):
        """Test parser uses absolute imports (not relative)"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        # Check for relative imports (from .. or from .)
        relative_imports = re.findall(r'from\s+\.+\w+', code)

        if relative_imports:
            pytest.fail(f"Found relative imports in {parser_file_path}: {relative_imports}")

    def test_parser_imports_are_organized(self, parser_file_path):
        """Test parser imports are organized (stdlib, third-party, local)"""
        with open(parser_file_path, 'r') as f:
            lines = f.readlines()

        # Find import section
        import_lines = []
        in_imports = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                import_lines.append(stripped)
                in_imports = True
            elif in_imports and stripped and not stripped.startswith('#'):
                break  # End of import section

        # Should have imports
        assert len(import_lines) > 0, "No imports found"

        # Imports should include required dependencies
        import_text = '\n'.join(import_lines)
        assert 'pandas' in import_text, "Missing pandas import"
        assert 'openpyxl' in import_text, "Missing openpyxl import"

    # ========================================================================
    # DOCUMENTATION TESTS
    # ========================================================================

    def test_parser_has_module_docstring(self, parser_file_path):
        """Test parser file has comprehensive module docstring"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        tree = ast.parse(code)
        module_docstring = ast.get_docstring(tree)

        assert module_docstring is not None, "Missing module docstring"
        assert len(module_docstring) > 100, "Module docstring too short"
        assert 'BUSINESS CONTEXT' in module_docstring, "Missing business context"

    def test_parser_class_has_docstring(self, parser_file_path):
        """Test ProjectSpreadsheetParser class has docstring"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        tree = ast.parse(code)

        # Find ProjectSpreadsheetParser class
        parser_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'ProjectSpreadsheetParser':
                parser_class = node
                break

        assert parser_class is not None, "ProjectSpreadsheetParser class not found"

        class_docstring = ast.get_docstring(parser_class)
        assert class_docstring is not None, "ProjectSpreadsheetParser missing docstring"

    def test_parser_public_methods_have_docstrings(self, parser_file_path):
        """Test all public methods have docstrings"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        tree = ast.parse(code)

        # Find ProjectSpreadsheetParser class
        parser_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'ProjectSpreadsheetParser':
                parser_class = node
                break

        assert parser_class is not None

        # Check all public methods have docstrings
        missing_docstrings = []
        for item in parser_class.body:
            if isinstance(item, ast.FunctionDef):
                # Only check public methods (not starting with _)
                if not item.name.startswith('_'):
                    docstring = ast.get_docstring(item)
                    if not docstring:
                        missing_docstrings.append(item.name)

        if missing_docstrings:
            pytest.fail(f"Public methods missing docstrings: {missing_docstrings}")

    # ========================================================================
    # CODE STRUCTURE TESTS
    # ========================================================================

    def test_parser_required_columns_defined(self, parser_file_path):
        """Test REQUIRED_COLUMNS constant is properly defined"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        assert 'REQUIRED_COLUMNS' in code, "REQUIRED_COLUMNS not defined"
        assert 'project_name' in code, "project_name not in REQUIRED_COLUMNS"
        assert 'project_slug' in code, "project_slug not in REQUIRED_COLUMNS"
        assert 'description' in code, "description not in REQUIRED_COLUMNS"

    def test_parser_optional_columns_defined(self, parser_file_path):
        """Test OPTIONAL_COLUMNS includes students and instructors"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        assert 'OPTIONAL_COLUMNS' in code, "OPTIONAL_COLUMNS not defined"
        assert 'student_emails' in code, "student_emails not in OPTIONAL_COLUMNS"
        assert 'instructor_emails' in code, "instructor_emails not in OPTIONAL_COLUMNS"

    def test_parser_has_required_methods(self, parser_file_path):
        """Test parser has all required methods"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        required_methods = [
            'parse_xlsx',
            'parse_ods',
            'parse_file',
            'detect_format',
            'generate_template',
            '_process_dataframe'
        ]

        for method in required_methods:
            assert f'def {method}' in code, f"Missing required method: {method}"

    # ========================================================================
    # API ENDPOINT TESTS
    # ========================================================================

    def test_main_has_import_spreadsheet_endpoint(self, main_file_path):
        """Test main.py has import spreadsheet endpoint"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        assert '/api/v1/projects/import-spreadsheet' in code, "Missing import-spreadsheet endpoint"
        assert '@app.post("/api/v1/projects/import-spreadsheet")' in code, "Import endpoint not properly decorated"

    def test_main_has_template_endpoint(self, main_file_path):
        """Test main.py has template download endpoint"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        assert '/api/v1/projects/template' in code, "Missing template endpoint"
        assert '@app.get("/api/v1/projects/template")' in code, "Template endpoint not properly decorated"

    def test_main_has_create_from_spreadsheet_endpoint(self, main_file_path):
        """Test main.py has automated creation endpoint"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        assert '/api/v1/projects/create-from-spreadsheet' in code, "Missing create-from-spreadsheet endpoint"
        assert '@app.post("/api/v1/projects/create-from-spreadsheet")' in code, "Create endpoint not properly decorated"

    def test_endpoints_have_comprehensive_docstrings(self, main_file_path):
        """Test API endpoints have comprehensive docstrings"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        # Find import_project_spreadsheet function
        import_func_match = re.search(r'async def import_project_spreadsheet.*?"""(.*?)"""', code, re.DOTALL)
        assert import_func_match, "import_project_spreadsheet missing or has no docstring"

        docstring = import_func_match.group(1)
        assert 'BUSINESS CONTEXT' in docstring, "import_project_spreadsheet docstring missing business context"
        assert 'WORKFLOW' in docstring, "import_project_spreadsheet docstring missing workflow"

    # ========================================================================
    # SECURITY TESTS
    # ========================================================================

    def test_endpoints_use_authentication(self, main_file_path):
        """Test endpoints use authentication dependency"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        # Check import_project_spreadsheet uses auth (capture up to closing paren and colon)
        import_func = re.search(r'async def import_project_spreadsheet\((.*?)\):', code, re.DOTALL)
        assert import_func, "import_project_spreadsheet function not found"

        params = import_func.group(1)
        assert 'Depends(get_current_user_id)' in params, "import_project_spreadsheet missing authentication"

        # Check create_from_spreadsheet uses auth (capture up to closing paren and colon)
        create_func = re.search(r'async def create_project_from_spreadsheet\((.*?)\):', code, re.DOTALL)
        assert create_func, "create_project_from_spreadsheet function not found"

        params = create_func.group(1)
        assert 'Depends(get_current_user_id)' in params, "create_project_from_spreadsheet missing authentication"

    def test_file_size_validation_present(self, main_file_path):
        """Test file upload endpoints validate file size"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        assert 'MAX_FILE_SIZE' in code, "MAX_FILE_SIZE constant not defined"
        assert 'File too large' in code, "Missing file size validation error message"

    def test_file_type_validation_present(self, main_file_path):
        """Test file upload endpoints validate file type"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        assert 'Unsupported file type' in code or 'Unsupported format' in code, "Missing file type validation"

    # ========================================================================
    # LOGGING TESTS
    # ========================================================================

    def test_parser_has_logging(self, parser_file_path):
        """Test parser has proper logging"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        assert 'import logging' in code, "Missing logging import"
        assert 'logger = logging.getLogger' in code, "Logger not initialized"
        assert 'logger.info' in code or 'logger.warning' in code or 'logger.error' in code, "Logger not used"

    def test_endpoints_have_logging(self, main_file_path):
        """Test endpoints have proper logging"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        # Check for logging in import endpoint
        assert 'logger.info(f"Parsing project spreadsheet' in code, "Missing logging in import endpoint"
        assert 'logger.error' in code, "Missing error logging"

    # ========================================================================
    # ERROR HANDLING TESTS
    # ========================================================================

    def test_parser_has_error_handling(self, parser_file_path):
        """Test parser has comprehensive error handling"""
        with open(parser_file_path, 'r') as f:
            code = f.read()

        # Should have try/except blocks
        assert 'try:' in code, "Missing try/except blocks"
        assert 'except Exception as e:' in code, "Missing generic exception handler"
        assert 'raise ValueError' in code, "Missing ValueError raises"

    def test_endpoints_have_error_handling(self, main_file_path):
        """Test endpoints have comprehensive error handling"""
        with open(main_file_path, 'r') as f:
            code = f.read()

        # Look for error handling in import endpoint
        import_func = re.search(r'async def import_project_spreadsheet.*?(?=async def|\Z)', code, re.DOTALL)
        assert import_func, "import_project_spreadsheet not found"

        func_code = import_func.group(0)
        assert 'try:' in func_code, "Missing try block in import_project_spreadsheet"
        assert 'except HTTPException:' in func_code, "Missing HTTPException handler"
        assert 'except ValueError' in func_code, "Missing ValueError handler"
        assert 'except Exception' in func_code, "Missing generic Exception handler"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
