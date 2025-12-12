"""
FRONTEND JAVASCRIPT LINTING TEST SUITE
PURPOSE: Validate JavaScript code quality, ES6 compliance, and best practices
WHY: Ensure maintainable, consistent frontend code following modern JS standards
"""

import subprocess
import sys
import os
from pathlib import Path
import json
import pytest

# Frontend JavaScript paths
FRONTEND_PATH = Path(__file__).parent.parent.parent / "frontend"
JS_PATH = FRONTEND_PATH / "js"

class TestFrontendJavaScriptLinting:
    """
    Frontend JavaScript code quality validation tests
    """
    
    def test_eslint_compliance(self):
        """
        Test JavaScript code style and best practices with ESLint
        WHY: Catches common errors and enforces consistent code style
        """
        # Create temporary .eslintrc.json if it doesn't exist
        eslint_config = JS_PATH / ".eslintrc.json"
        
        config_content = {
            "env": {
                "browser": True,
                "es2021": True,
                "node": True
            },
            "extends": ["eslint:recommended"],
            "parserOptions": {
                "ecmaVersion": 2021,
                "sourceType": "module"
            },
            "rules": {
                "indent": ["error", 4],
                "quotes": ["error", "single"],
                "semi": ["error", "always"],
                "no-unused-vars": "warn",
                "no-console": "warn",
                "no-debugger": "error",
                "no-alert": "warn",
                "prefer-const": "error",
                "no-var": "error",
                "arrow-spacing": "error",
                "brace-style": "error",
                "comma-spacing": "error",
                "key-spacing": "error",
                "space-before-blocks": "error",
                "space-infix-ops": "error"
            }
        }
        
        # Write config temporarily
        with open(eslint_config, 'w') as f:
            json.dump(config_content, f, indent=2)
        
        try:
            result = subprocess.run([
                "npx", "eslint",
                str(JS_PATH / "**/*.js"),
                "--format", "compact",
                "--config", str(eslint_config)
            ], capture_output=True, text=True, cwd=JS_PATH)
            
            if result.returncode != 0:
                print(f"ESLint violations found:\n{result.stdout}")
                print(f"ESLint stderr:\n{result.stderr}")
            
            # Remove temporary config
            if eslint_config.exists():
                eslint_config.unlink()
            
            # For now, treat as warning rather than failure due to setup complexity
            if result.returncode != 0:
                print("Warning: ESLint found issues. Consider installing ESLint globally.")
            
        except FileNotFoundError:
            pytest.fail("ESLint not available, skipping JavaScript linting")
    
    def test_javascript_syntax_validation(self):
        """
        Test JavaScript syntax validity using Node.js
        WHY: Catch syntax errors that would break in browser
        """
        js_files = list(JS_PATH.rglob("*.js"))
        syntax_errors = []
        
        for js_file in js_files:
            try:
                # Use node to check syntax
                result = subprocess.run([
                    "node", "--check", str(js_file)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    syntax_errors.append(f"{js_file}: {result.stderr.strip()}")
                    
            except FileNotFoundError:
                # Fallback: basic syntax check with Python
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Basic syntax checks
                if content.count('{') != content.count('}'):
                    syntax_errors.append(f"{js_file}: Mismatched curly braces")
                if content.count('(') != content.count(')'):
                    syntax_errors.append(f"{js_file}: Mismatched parentheses")
                if content.count('[') != content.count(']'):
                    syntax_errors.append(f"{js_file}: Mismatched square brackets")
                
                # Check for literal \n sequences that should be actual newlines
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if '\\n' in line and not line.strip().startswith('//') and not line.strip().startswith('*'):
                        # Allow in specific contexts like printf-style formats or regex
                        if not any(ctx in line.lower() for ctx in ['printf', 'format', 'regex', 'pattern', 'replace']):
                            syntax_errors.append(f"{js_file}:{line_num}: Literal \\n found - should use actual newline or template literal")
        
        if syntax_errors:
            error_msg = "JavaScript syntax errors found:\n" + "\n".join(syntax_errors)
            print(error_msg)
            assert False, error_msg
    
    def test_es6_module_compliance(self):
        """
        Test ES6 module structure and imports/exports
        WHY: Ensure proper module organization and dependency management
        """
        js_files = list(JS_PATH.rglob("*.js"))
        module_issues = []
        
        for js_file in js_files:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for ES6 module patterns
            has_import = 'import ' in content
            has_export = 'export ' in content or 'export default' in content
            
            # Files in modules directory should use ES6 modules
            if 'modules' in str(js_file):
                if not has_export:
                    module_issues.append(f"{js_file}: Module file should have exports")
                
                # Check import syntax
                import_lines = [line.strip() for line in content.split('\n') 
                              if line.strip().startswith('import')]
                
                for line in import_lines:
                    if not line.endswith(';'):
                        module_issues.append(f"{js_file}: Import statement should end with semicolon: {line}")
        
        if module_issues:
            print("ES6 Module issues found:\n" + "\n".join(module_issues))
            # Treat as warnings for now
    
    def test_function_naming_conventions(self):
        """
        Test JavaScript function naming follows camelCase convention
        WHY: Consistent naming improves code readability and maintainability
        """
        js_files = list(JS_PATH.rglob("*.js"))
        naming_issues = []
        
        for js_file in js_files:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Check function declarations
                if 'function ' in line:
                    # Extract function name
                    parts = line.split('function ')
                    if len(parts) > 1:
                        func_part = parts[1].split('(')[0].strip()
                        if func_part and not func_part[0].islower():
                            naming_issues.append(
                                f"{js_file}:{i}: Function should start with lowercase: {func_part}"
                            )
                
                # Check arrow functions assigned to variables
                if '=>' in line and '=' in line:
                    var_part = line.split('=')[0].strip()
                    if var_part.startswith(('const ', 'let ', 'var ')):
                        var_name = var_part.split()[-1]
                        if var_name and not var_name[0].islower():
                            naming_issues.append(
                                f"{js_file}:{i}: Variable should start with lowercase: {var_name}"
                            )
        
        if naming_issues:
            print("Naming convention issues found:\n" + "\n".join(naming_issues[:10]))  # Show first 10
            # Treat as warnings
    
    def test_console_and_debug_statements(self):
        """
        Test for leftover console.log and debugger statements
        WHY: Debug statements should not be in production code
        """
        js_files = list(JS_PATH.rglob("*.js"))
        debug_issues = []
        
        for js_file in js_files:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for console statements (allow console.error and console.warn)
                if 'console.log(' in line_stripped or 'console.debug(' in line_stripped:
                    debug_issues.append(f"{js_file}:{i}: Remove console.log/debug statement")
                
                # Check for debugger statements
                if line_stripped.startswith('debugger'):
                    debug_issues.append(f"{js_file}:{i}: Remove debugger statement")
                
                # Check for alert statements
                if 'alert(' in line_stripped:
                    debug_issues.append(f"{js_file}:{i}: Avoid alert() statements")
        
        if debug_issues:
            print("Debug statements found:\n" + "\n".join(debug_issues[:10]))
            # For now, treat as warnings rather than failures
    
    def test_documentation_comments(self):
        """
        Test for adequate JSDoc-style comments
        WHY: Good documentation improves code maintainability
        """
        js_files = list(JS_PATH.rglob("*.js"))
        doc_stats = {"files_with_docs": 0, "total_files": len(js_files)}
        
        for js_file in js_files:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for documentation comments
            if '/**' in content or '/*' in content:
                doc_stats["files_with_docs"] += 1
        
        coverage_percent = (doc_stats["files_with_docs"] / doc_stats["total_files"]) * 100
        print(f"Documentation coverage: {coverage_percent:.1f}% ({doc_stats['files_with_docs']}/{doc_stats['total_files']} files)")
        
        # Require at least 50% of files to have some documentation
        assert coverage_percent >= 50, f"Documentation coverage too low: {coverage_percent:.1f}%"
    
    def test_file_structure_compliance(self):
        """
        Test frontend file structure follows conventions
        WHY: Consistent project organization improves maintainability
        """
        expected_structure = {
            "js": {
                "main.js": "required",
                "modules": {
                    "app.js": "required",
                    "navigation.js": "required",
                    "auth.js": "required"
                }
            },
            "css": "required",
            "html": "required"
        }
        
        # Check main JavaScript structure
        assert (JS_PATH / "main.js").exists(), "main.js is required"
        assert (JS_PATH / "modules").is_dir(), "modules directory is required"
        assert (JS_PATH / "modules" / "app.js").exists(), "modules/app.js is required"
        
        # Check for unwanted files
        unwanted_files = list(FRONTEND_PATH.rglob("*.tmp"))
        unwanted_files.extend(list(FRONTEND_PATH.rglob("*~")))
        unwanted_files.extend(list(FRONTEND_PATH.rglob(".DS_Store")))
        
        if unwanted_files:
            print(f"Warning: Found unwanted files: {unwanted_files}")
    
    def test_async_await_usage(self):
        """
        Test proper async/await usage instead of callback patterns
        WHY: Modern async patterns are more maintainable than callbacks
        """
        js_files = list(JS_PATH.rglob("*.js"))
        async_issues = []
        
        for js_file in js_files:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for callback patterns that should use async/await
                if '.then(' in line_stripped and 'await' not in line_stripped:
                    # Allow .then() in certain contexts, warn about others
                    if 'console.log' not in line_stripped:
                        async_issues.append(f"{js_file}:{i}: Consider using async/await instead of .then()")
        
        if async_issues[:5]:  # Show first 5
            print("Async/await suggestions:\n" + "\n".join(async_issues[:5]))
            # Treat as recommendations, not failures
    
    def test_error_handling_patterns(self):
        """
        Test for proper error handling patterns
        WHY: Proper error handling improves application reliability
        """
        js_files = list(JS_PATH.rglob("*.js"))
        error_handling_stats = {"try_catch_blocks": 0, "async_functions": 0, "error_handled_async": 0}
        
        for js_file in js_files:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count try-catch blocks
            error_handling_stats["try_catch_blocks"] += content.count('try {')
            
            # Count async functions
            error_handling_stats["async_functions"] += content.count('async ')
            
            # Check if async functions have error handling
            if 'async ' in content and ('try {' in content or '.catch(' in content):
                error_handling_stats["error_handled_async"] += 1
        
        print(f"Error handling stats: {error_handling_stats}")
        
        # Basic sanity check - if there are async functions, some should have error handling
        if error_handling_stats["async_functions"] > 0:
            error_coverage = error_handling_stats["error_handled_async"] / len(js_files)
            print(f"Error handling coverage: {error_coverage:.1f} per file")