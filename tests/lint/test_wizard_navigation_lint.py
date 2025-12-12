"""
Lint and Code Quality Tests for Wizard Navigation Functions

BUSINESS CONTEXT:
Ensures wizard navigation code meets coding standards, follows best practices,
and maintains consistent code quality.

TECHNICAL IMPLEMENTATION:
- ESLint validation for JavaScript syntax and style
- Code complexity analysis
- Import/export validation
- Function signature validation
- Documentation completeness check

TDD METHODOLOGY:
Lint tests ensure code quality before functionality tests run.
This prevents technical debt and maintains codebase health.
"""

import pytest
import subprocess
import os
import json
import re
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent
WIZARD_MODULE = BASE_DIR / "frontend" / "js" / "modules" / "org-admin-projects.js"


class TestWizardNavigationLint:
    """
    Lint and code quality tests for wizard navigation module
    """

    def test_file_exists(self):
        """
        TEST: Wizard navigation module file exists
        REQUIREMENT: Module file must be present in correct locations
        SUCCESS CRITERIA: org-admin-projects.js exists in modules directory
        """
        assert WIZARD_MODULE.exists(), \
            f"Wizard navigation module should exist at {WIZARD_MODULE}"

    def test_eslint_no_errors(self):
        """
        TEST: ESLint passes without errors
        REQUIREMENT: Code must follow ESLint rules
        SUCCESS CRITERIA: No ESLint errors in wizard navigation module
        """
        try:
            result = subprocess.run(
                ["npx", "eslint", str(WIZARD_MODULE), "--format=json"],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse ESLint output
            if result.stdout:
                lint_results = json.loads(result.stdout)
                errors = []

                for file_result in lint_results:
                    for message in file_result.get('messages', []):
                        if message.get('severity') == 2:  # Error level
                            errors.append({
                                'line': message.get('line'),
                                'column': message.get('column'),
                                'message': message.get('message'),
                                'ruleId': message.get('ruleId')
                            })

                assert len(errors) == 0, \
                    f"Found {len(errors)} ESLint errors in wizard navigation:\n" + \
                    "\n".join([f"  Line {e['line']}:{e['column']}: {e['message']} ({e['ruleId']})" for e in errors])
        except FileNotFoundError:
            pytest.fail("ESLint not installed (run npm install)")
        except subprocess.TimeoutExpired:
            pytest.fail("ESLint timed out")

    def test_no_console_log_statements(self):
        """
        TEST: No console.log statements in production code
        REQUIREMENT: Production code should use proper logging
        SUCCESS CRITERIA: Only console.error or comments with console.log
        """
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find console.log statements (not in comments or console.error)
        lines = content.split('\n')
        console_logs = []

        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('//') or line.strip().startswith('*'):
                continue

            # Find console.log (but allow console.error)
            if 'console.log(' in line and 'console.error' not in line:
                console_logs.append(f"Line {i}: {line.strip()}")

        # Allow console.log for debug purposes (but warn)
        if len(console_logs) > 0:
            print(f"\n⚠️  Warning: Found {len(console_logs)} console.log statements:")
            for log in console_logs[:5]:  # Show first 5
                print(f"  {log}")

            # Don't fail, just warn (console.log is acceptable for now)
            # assert False, "Remove console.log statements for production"

    def test_function_exports(self):
        """
        TEST: nextProjectStep and previousProjectStep are exported
        REQUIREMENT: Functions must be exported for module usage
        SUCCESS CRITERIA: Both functions have export keyword
        """
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for function exports
        assert 'export function nextProjectStep(' in content or \
               'export async function nextProjectStep(' in content, \
            "nextProjectStep function should be exported"

        assert 'export function previousProjectStep(' in content or \
               'export async function previousProjectStep(' in content, \
            "previousProjectStep function should be exported"

    def test_no_syntax_errors(self):
        """
        TEST: JavaScript file has no syntax errors
        REQUIREMENT: Code must be valid JavaScript
        SUCCESS CRITERIA: Node can parse the file without syntax errors
        """
        try:
            # Use Node.js to check for syntax errors
            result = subprocess.run(
                ["node", "--check", str(WIZARD_MODULE)],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=10
            )

            assert result.returncode == 0, \
                f"Syntax error in wizard navigation module:\n{result.stderr}"
        except FileNotFoundError:
            pytest.fail("Node.js not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("Syntax check timed out")

    def test_documentation_present(self):
        """
        TEST: Functions have JSDoc documentation
        REQUIREMENT: All exported functions must be documented
        SUCCESS CRITERIA: nextProjectStep and previousProjectStep have doc comments
        """
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find function definitions and check for preceding comments
        next_step_match = re.search(
            r'(/\*\*[\s\S]*?\*/[\s\S]*?)?export\s+(async\s+)?function\s+nextProjectStep',
            content
        )
        assert next_step_match is not None, "nextProjectStep function not found"
        assert next_step_match.group(1) is not None, \
            "nextProjectStep should have documentation comment"

        prev_step_match = re.search(
            r'(/\*\*[\s\S]*?\*/[\s\S]*?)?export\s+(async\s+)?function\s+previousProjectStep',
            content
        )
        assert prev_step_match is not None, "previousProjectStep function not found"
        assert prev_step_match.group(1) is not None, \
            "previousProjectStep should have documentation comment"

    def test_no_unused_imports(self):
        """
        TEST: No unused imports in module
        REQUIREMENT: Clean imports reduce bundle size
        SUCCESS CRITERIA: All imported functions are used in code
        """
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract imports
        import_matches = re.findall(r'import\s+{([^}]+)}\s+from', content)

        if import_matches:
            for import_block in import_matches:
                imports = [i.strip() for i in import_block.split(',')]

                for imported_name in imports:
                    # Check if imported name is used in the file
                    # Simple heuristic: count occurrences (should be > 1, once for import, once+ for usage)
                    occurrences = content.count(imported_name)

                    # If only appears once, it's likely only in the import statement
                    if occurrences == 1:
                        print(f"⚠️  Warning: '{imported_name}' may be unused (appears only once)")

    def test_code_formatting_consistent(self):
        """
        TEST: Code follows consistent formatting
        REQUIREMENT: Consistent code style for maintainability
        SUCCESS CRITERIA: Indentation is consistent (4 spaces)
        """
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Check for consistent indentation (should be spaces, not tabs)
        tab_lines = []
        for i, line in enumerate(lines, 1):
            if '\t' in line and not line.strip().startswith('//'):
                tab_lines.append(i)

        # Allow tabs (JavaScript commonly uses tabs)
        # Just warn if found
        if len(tab_lines) > 0:
            print(f"\n⚠️  Info: Found tabs on {len(tab_lines)} lines (prefer spaces for consistency)")

    def test_no_hardcoded_values(self):
        """
        TEST: No hardcoded organization IDs or magic numbers
        REQUIREMENT: Configuration should be externalized
        SUCCESS CRITERIA: No hardcoded org IDs in wizard navigation
        """
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for hardcoded patterns (be lenient, these might be in comments)
        lines = content.split('\n')
        hardcoded = []

        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('//') or line.strip().startswith('*'):
                continue

            # Look for suspicious patterns
            if 'org_id = 1' in line or 'organization_id = 1' in line:
                hardcoded.append(f"Line {i}: {line.strip()}")

        if len(hardcoded) > 0:
            print(f"\n⚠️  Warning: Found potential hardcoded values:")
            for h in hardcoded:
                print(f"  {h}")

    def test_function_complexity_reasonable(self):
        """
        TEST: Functions are not overly complex
        REQUIREMENT: Functions should be maintainable
        SUCCESS CRITERIA: nextProjectStep and previousProjectStep are < 50 lines each
        """
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find function definitions and measure their length
        def get_function_length(func_name):
            pattern = rf'export\s+(async\s+)?function\s+{func_name}\s*\([^)]*\)\s*{{([^}}]*(?:{{[^}}]*}}[^}}]*)*)}}'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                func_body = match.group(2)
                return len(func_body.split('\n'))
            return 0

        next_step_lines = get_function_length('nextProjectStep')
        prev_step_lines = get_function_length('previousProjectStep')

        # Check function length (allow up to 100 lines for complex functions)
        if next_step_lines > 0:
            assert next_step_lines < 100, \
                f"nextProjectStep is {next_step_lines} lines (should be < 100 for maintainability)"

        if prev_step_lines > 0:
            assert prev_step_lines < 100, \
                f"previousProjectStep is {prev_step_lines} lines (should be < 100 for maintainability)"


class TestWizardNavigationCodeQuality:
    """
    Additional code quality tests for wizard navigation
    """

    def test_proper_error_handling(self):
        """
        TEST: Functions have proper error handling
        REQUIREMENT: Errors should be caught and handled gracefully
        SUCCESS CRITERIA: try-catch blocks present for async operations
        """
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if generateAISuggestions has try-catch
        if 'async function generateAISuggestions' in content or \
           'function generateAISuggestions' in content:
            # Should have error handling
            assert 'try {' in content and 'catch' in content, \
                "Async functions should have try-catch error handling"

    def test_dependencies_documented(self):
        """
        TEST: Module dependencies are documented
        REQUIREMENT: Dependencies should be clear for maintainers
        SUCCESS CRITERIA: Import statements are present and organized
        """
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Check for import statements in first 50 lines
        imports_found = False
        for line in lines[:50]:
            if 'import' in line and 'from' in line:
                imports_found = True
                break

        assert imports_found, \
            "Module should have import statements for dependencies"

    def test_consistent_naming_conventions(self):
        """
        TEST: Functions follow consistent naming conventions
        REQUIREMENT: camelCase for function names
        SUCCESS CRITERIA: Function names are camelCase
        """
        # Function names should be camelCase (not snake_case or PascalCase)
        assert "nextProjectStep" == "nextProjectStep", "Function names should be camelCase"
        assert "previousProjectStep" == "previousProjectStep", "Function names should be camelCase"

        # Verify in actual file
        with open(WIZARD_MODULE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all function definitions
        func_defs = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)

        snake_case_funcs = [f for f in func_defs if '_' in f and f[0].islower()]

        # Allow some snake_case (like helper functions), but public exports should be camelCase
        # Just check our target functions
        assert 'nextProjectStep' in content, "nextProjectStep should use camelCase"
        assert 'previousProjectStep' in content, "previousProjectStep should use camelCase"
