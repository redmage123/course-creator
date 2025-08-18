"""
Lint Tests for Student Login System

This module contains comprehensive linting and code quality tests for the
student login system, ensuring adherence to coding standards, security
best practices, and GDPR compliance in code structure.

Business Context:
Validates that the student login implementation follows established coding
standards, maintains security best practices, and implements GDPR compliance
correctly at the code level through static analysis and pattern detection.

Test Coverage:
- Python code quality (PEP 8, security patterns)
- JavaScript code quality (ESLint standards)
- HTML accessibility and semantic structure
- CSS compliance and responsive design patterns
- Security anti-patterns detection
- GDPR compliance code patterns
- Documentation completeness
"""

import pytest
import os
import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import ast
import tempfile


class LintTestBase:
    """Base class for lint testing functionality."""
    
    def setup_method(self):
        """Set up lint test environment."""
        self.project_root = Path(__file__).parent.parent.parent
        self.student_login_files = {
            'python': [
                self.project_root / 'services/user-management/routes.py',
                self.project_root / 'tests/unit/user_management/test_student_login.py',
                self.project_root / 'tests/integration/test_student_login_gdpr.py'
            ],
            'javascript': [
                self.project_root / 'frontend/html/student-login.html'  # Contains JS
            ],
            'html': [
                self.project_root / 'frontend/html/student-login.html'
            ],
            'css': [
                self.project_root / 'frontend/html/student-login.html'  # Contains CSS
            ]
        }


@pytest.mark.lint
class TestPythonCodeQuality(LintTestBase):
    """Test Python code quality for student login system."""
    
    def test_python_flake8_compliance(self):
        """Test Python files comply with Flake8 standards."""
        # Arrange
        python_files = [str(f) for f in self.student_login_files['python'] if f.exists()]
        
        if not python_files:
            pytest.skip("No Python files found for student login system")
        
        # Act
        result = subprocess.run(
            ['flake8', '--max-line-length=120', '--extend-ignore=E203,W503'] + python_files,
            capture_output=True,
            text=True
        )
        
        # Assert
        if result.returncode != 0:
            pytest.fail(f"Flake8 violations found:\n{result.stdout}\n{result.stderr}")

    def test_python_security_patterns(self):
        """Test for security anti-patterns in Python code."""
        # Arrange
        python_files = [f for f in self.student_login_files['python'] if f.exists()]
        
        security_violations = []
        
        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Act - Check for security anti-patterns
                # Check for hardcoded secrets
                if re.search(r'(password|secret|key)\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
                    security_violations.append(f"{file_path}: Potential hardcoded secret")
                
                # Check for SQL injection patterns
                if re.search(r'f["\'].*\{.*\}.*["\'].*execute|format.*execute', content):
                    security_violations.append(f"{file_path}: Potential SQL injection vulnerability")
                
                # Check for unsafe eval usage
                if 'eval(' in content:
                    security_violations.append(f"{file_path}: Unsafe eval() usage")
                
                # Check for generic exception catching
                if re.search(r'except\s+Exception\s*:', content):
                    # Allow in test files and specific documented cases
                    if 'test_' not in str(file_path) and 'except Exception as e:' not in content:
                        security_violations.append(f"{file_path}: Generic exception handling")
        
        # Assert
        if security_violations:
            pytest.fail(f"Security violations found:\n" + "\n".join(security_violations))

    def test_gdpr_compliance_patterns(self):
        """Test for GDPR compliance patterns in Python code."""
        # Arrange
        python_files = [f for f in self.student_login_files['python'] if f.exists()]
        
        gdpr_compliance_issues = []
        
        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Act - Check for GDPR compliance patterns
                # Check for consent handling
                if 'consent' in content.lower():
                    if not re.search(r'consent.*=.*false|consent.*default.*false', content, re.IGNORECASE):
                        if 'test' not in str(file_path):  # Allow in tests
                            gdpr_compliance_issues.append(f"{file_path}: Consent should default to False")
                
                # Check for data minimization comments
                if 'personal' in content.lower() or 'sensitive' in content.lower():
                    if not re.search(r'(minimization|gdpr|privacy)', content, re.IGNORECASE):
                        gdpr_compliance_issues.append(f"{file_path}: Personal data handling without privacy context")
                
                # Check for logging of sensitive data
                if re.search(r'log.*\.(info|debug|error).*password|log.*\.(info|debug|error).*email', content, re.IGNORECASE):
                    gdpr_compliance_issues.append(f"{file_path}: Potential logging of sensitive data")
        
        # Assert
        if gdpr_compliance_issues:
            pytest.fail(f"GDPR compliance issues found:\n" + "\n".join(gdpr_compliance_issues))

    def test_documentation_completeness(self):
        """Test that Python functions have adequate documentation."""
        # Arrange
        python_files = [f for f in self.student_login_files['python'] if f.exists()]
        
        documentation_issues = []
        
        for file_path in python_files:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read())
                        
                        # Act - Check for function documentation
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                # Skip test functions and private functions
                                if node.name.startswith('test_') or node.name.startswith('_'):
                                    continue
                                
                                # Check for docstring
                                if not ast.get_docstring(node):
                                    documentation_issues.append(
                                        f"{file_path}:{node.lineno}: Function '{node.name}' missing docstring"
                                    )
                                else:
                                    docstring = ast.get_docstring(node)
                                    # Check for GDPR context in privacy-related functions
                                    if any(keyword in node.name.lower() for keyword in ['login', 'consent', 'privacy', 'analytics']):
                                        if len(docstring) < 50:  # Minimum meaningful documentation
                                            documentation_issues.append(
                                                f"{file_path}:{node.lineno}: Function '{node.name}' has insufficient documentation"
                                            )
                    except SyntaxError:
                        documentation_issues.append(f"{file_path}: Syntax error in file")
        
        # Assert
        if documentation_issues:
            pytest.fail(f"Documentation issues found:\n" + "\n".join(documentation_issues))


@pytest.mark.lint
class TestJavaScriptCodeQuality(LintTestBase):
    """Test JavaScript code quality for student login system."""
    
    def test_javascript_syntax_validation(self):
        """Test JavaScript syntax validation."""
        # Arrange
        html_files = [f for f in self.student_login_files['html'] if f.exists()]
        
        js_syntax_errors = []
        
        for file_path in html_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract JavaScript from HTML
                js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
                
                for i, js_block in enumerate(js_blocks):
                    # Skip empty blocks or src-only scripts
                    if not js_block.strip() or 'src=' in js_block:
                        continue
                    
                    # Create temporary JS file for validation
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_js:
                        temp_js.write(js_block)
                        temp_js_path = temp_js.name
                    
                    try:
                        # Use Node.js to validate syntax
                        result = subprocess.run(
                            ['node', '-c', temp_js_path],
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode != 0:
                            js_syntax_errors.append(f"{file_path} (script block {i+1}): {result.stderr}")
                    
                    except FileNotFoundError:
                        # Node.js not available, skip syntax check
                        pass
                    
                    finally:
                        os.unlink(temp_js_path)
        
        # Assert
        if js_syntax_errors:
            pytest.fail(f"JavaScript syntax errors found:\n" + "\n".join(js_syntax_errors))

    def test_javascript_security_patterns(self):
        """Test for security anti-patterns in JavaScript code."""
        # Arrange
        html_files = [f for f in self.student_login_files['html'] if f.exists()]
        
        security_violations = []
        
        for file_path in html_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Act - Check for security anti-patterns
                # Check for eval() usage
                if re.search(r'\beval\s*\(', content):
                    security_violations.append(f"{file_path}: Unsafe eval() usage")
                
                # Check for innerHTML with user data
                if re.search(r'innerHTML\s*=.*\+|innerHTML\s*=.*\$\{', content):
                    security_violations.append(f"{file_path}: Potential XSS via innerHTML")
                
                # Check for document.write
                if 'document.write' in content:
                    security_violations.append(f"{file_path}: Unsafe document.write usage")
                
                # Check for hardcoded API keys or secrets
                if re.search(r'(api_key|secret|token)\s*[:=]\s*["\'][^"\']{20,}["\']', content, re.IGNORECASE):
                    security_violations.append(f"{file_path}: Potential hardcoded API key")
        
        # Assert
        if security_violations:
            pytest.fail(f"JavaScript security violations found:\n" + "\n".join(security_violations))

    def test_javascript_gdpr_patterns(self):
        """Test for GDPR compliance patterns in JavaScript code."""
        # Arrange
        html_files = [f for f in self.student_login_files['html'] if f.exists()]
        
        gdpr_issues = []
        
        for file_path in html_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Act - Check for GDPR compliance patterns
                # Check for consent handling
                if 'consent' in content.lower():
                    # Should have explicit consent checking
                    if not re.search(r'consent.*checked|consent.*true', content, re.IGNORECASE):
                        gdpr_issues.append(f"{file_path}: Consent handling without explicit checks")
                
                # Check for analytics tracking
                if re.search(r'(analytics|tracking|gtag|ga\()', content, re.IGNORECASE):
                    # Should have consent checks before analytics
                    if not re.search(r'consent.*analytics|analytics.*consent', content, re.IGNORECASE):
                        gdpr_issues.append(f"{file_path}: Analytics without consent checks")
                
                # Check for device fingerprinting
                if re.search(r'(fingerprint|device.*id|browser.*info)', content, re.IGNORECASE):
                    # Should be anonymized
                    if not re.search(r'(anonymized|hash|btoa)', content, re.IGNORECASE):
                        gdpr_issues.append(f"{file_path}: Device fingerprinting without anonymization")
        
        # Assert
        if gdpr_issues:
            pytest.fail(f"JavaScript GDPR issues found:\n" + "\n".join(gdpr_issues))


@pytest.mark.lint
class TestHTMLQuality(LintTestBase):
    """Test HTML quality for student login system."""
    
    def test_html_accessibility_compliance(self):
        """Test HTML accessibility compliance."""
        # Arrange
        html_files = [f for f in self.student_login_files['html'] if f.exists()]
        
        accessibility_issues = []
        
        for file_path in html_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Act - Check accessibility patterns
                # Check for form labels
                inputs = re.findall(r'<input[^>]+id=["\']([^"\']+)["\'][^>]*>', content)
                for input_id in inputs:
                    label_pattern = f'<label[^>]+for=["\']?{input_id}["\']?[^>]*>'
                    if not re.search(label_pattern, content):
                        accessibility_issues.append(f"{file_path}: Input '{input_id}' missing associated label")
                
                # Check for alt text on images
                img_tags = re.findall(r'<img[^>]*>', content)
                for img_tag in img_tags:
                    if 'alt=' not in img_tag:
                        accessibility_issues.append(f"{file_path}: Image missing alt attribute")
                
                # Check for semantic HTML
                if '<div class="button"' in content and '<button' not in content:
                    accessibility_issues.append(f"{file_path}: Using div instead of button element")
                
                # Check for ARIA attributes where needed
                modals = re.findall(r'<div[^>]+class=["\'][^"\']*modal[^"\']*["\'][^>]*>', content)
                for modal in modals:
                    if 'role=' not in modal and 'aria-' not in modal:
                        accessibility_issues.append(f"{file_path}: Modal missing ARIA attributes")
        
        # Assert
        if accessibility_issues:
            pytest.fail(f"HTML accessibility issues found:\n" + "\n".join(accessibility_issues))

    def test_html_semantic_structure(self):
        """Test HTML semantic structure."""
        # Arrange
        html_files = [f for f in self.student_login_files['html'] if f.exists()]
        
        semantic_issues = []
        
        for file_path in html_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Act - Check semantic structure
                # Check for proper heading hierarchy
                headings = re.findall(r'<h([1-6])[^>]*>', content)
                if headings:
                    heading_levels = [int(h) for h in headings]
                    if heading_levels and heading_levels[0] != 1:
                        semantic_issues.append(f"{file_path}: Page should start with h1")
                
                # Check for main content area
                if '<main' not in content and 'role="main"' not in content:
                    semantic_issues.append(f"{file_path}: Missing main content area")
                
                # Check for form structure
                if '<form' in content:
                    # Forms should have fieldsets for grouped content
                    if 'consent' in content.lower() and '<fieldset' not in content:
                        semantic_issues.append(f"{file_path}: Consent form should use fieldset")
        
        # Assert
        if semantic_issues:
            pytest.fail(f"HTML semantic structure issues found:\n" + "\n".join(semantic_issues))

    def test_html_gdpr_compliance(self):
        """Test HTML structure for GDPR compliance."""
        # Arrange
        html_files = [f for f in self.student_login_files['html'] if f.exists()]
        
        gdpr_html_issues = []
        
        for file_path in html_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Act - Check GDPR compliance in HTML
                # Check for privacy notice
                if not re.search(r'privacy.*notice|data.*processing.*notice', content, re.IGNORECASE):
                    gdpr_html_issues.append(f"{file_path}: Missing privacy notice")
                
                # Check for consent checkboxes
                consent_checkboxes = re.findall(r'<input[^>]+type=["\']checkbox["\'][^>]*consent[^>]*>', content, re.IGNORECASE)
                if not consent_checkboxes:
                    gdpr_html_issues.append(f"{file_path}: Missing consent checkboxes")
                
                # Check that consent checkboxes are not pre-checked
                for checkbox in consent_checkboxes:
                    if 'checked' in checkbox:
                        gdpr_html_issues.append(f"{file_path}: Consent checkbox pre-checked (violates GDPR)")
                
                # Check for privacy policy link
                if not re.search(r'<a[^>]+privacy.*policy|privacy.*policy[^>]*</a>', content, re.IGNORECASE):
                    gdpr_html_issues.append(f"{file_path}: Missing privacy policy link")
        
        # Assert
        if gdpr_html_issues:
            pytest.fail(f"HTML GDPR compliance issues found:\n" + "\n".join(gdpr_html_issues))


@pytest.mark.lint
class TestCSSQuality(LintTestBase):
    """Test CSS quality for student login system."""
    
    def test_css_responsive_design_patterns(self):
        """Test CSS responsive design patterns."""
        # Arrange
        html_files = [f for f in self.student_login_files['html'] if f.exists()]
        
        responsive_issues = []
        
        for file_path in html_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract CSS from HTML
                css_blocks = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
                
                for css_block in css_blocks:
                    # Act - Check responsive design patterns
                    # Check for media queries
                    if '@media' not in css_block:
                        responsive_issues.append(f"{file_path}: CSS missing media queries for responsive design")
                    
                    # Check for flexible units
                    if re.search(r'width\s*:\s*\d+px', css_block) and 'max-width' not in css_block:
                        responsive_issues.append(f"{file_path}: Fixed width without max-width constraint")
                    
                    # Check for accessibility-friendly focus styles
                    if ':focus' not in css_block:
                        responsive_issues.append(f"{file_path}: Missing focus styles for accessibility")
        
        # Assert
        if responsive_issues:
            pytest.fail(f"CSS responsive design issues found:\n" + "\n".join(responsive_issues))

    def test_css_accessibility_patterns(self):
        """Test CSS accessibility patterns."""
        # Arrange
        html_files = [f for f in self.student_login_files['html'] if f.exists()]
        
        accessibility_css_issues = []
        
        for file_path in html_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                css_blocks = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
                
                for css_block in css_blocks:
                    # Act - Check accessibility patterns
                    # Check for sufficient color contrast (basic pattern check)
                    if re.search(r'color\s*:\s*#fff|color\s*:\s*white', css_block, re.IGNORECASE):
                        if not re.search(r'background.*#[0-5][0-5][0-5]|background.*black', css_block, re.IGNORECASE):
                            accessibility_css_issues.append(f"{file_path}: Potential low contrast with white text")
                    
                    # Check for font size accessibility
                    if re.search(r'font-size\s*:\s*[0-9]px', css_block):
                        accessibility_css_issues.append(f"{file_path}: Fixed pixel font sizes may not scale")
                    
                    # Check for hover-only interactions
                    hover_selectors = re.findall(r'([^{}]+):hover[^{]*{', css_block)
                    for selector in hover_selectors:
                        focus_variant = selector + ':focus'
                        if focus_variant not in css_block:
                            accessibility_css_issues.append(f"{file_path}: Hover effect without focus equivalent")
        
        # Assert
        if accessibility_css_issues:
            pytest.fail(f"CSS accessibility issues found:\n" + "\n".join(accessibility_css_issues))


@pytest.mark.lint
class TestSecurityPatterns(LintTestBase):
    """Test security patterns across all student login files."""
    
    def test_no_hardcoded_secrets(self):
        """Test that no secrets are hardcoded in any files."""
        # Arrange
        all_files = []
        for file_list in self.student_login_files.values():
            all_files.extend([f for f in file_list if f.exists()])
        
        secret_violations = []
        
        # Common secret patterns
        secret_patterns = [
            r'password\s*[:=]\s*["\'][^"\']{8,}["\']',
            r'secret\s*[:=]\s*["\'][^"\']{16,}["\']',
            r'api_key\s*[:=]\s*["\'][^"\']{16,}["\']',
            r'token\s*[:=]\s*["\'][^"\']{20,}["\']',
            r'(sk_|pk_|api_)[a-zA-Z0-9]{20,}',  # Common API key formats
        ]
        
        for file_path in all_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for pattern in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip test data and examples
                        if 'test' in match.group().lower() or 'example' in match.group().lower():
                            continue
                        
                        secret_violations.append(
                            f"{file_path}: Potential hardcoded secret: {match.group()[:50]}..."
                        )
        
        # Assert
        if secret_violations:
            pytest.fail(f"Hardcoded secrets found:\n" + "\n".join(secret_violations))

    def test_secure_communication_patterns(self):
        """Test for secure communication patterns."""
        # Arrange
        all_files = []
        for file_list in self.student_login_files.values():
            all_files.extend([f for f in file_list if f.exists()])
        
        insecure_communication = []
        
        for file_path in all_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for HTTP URLs in production code
                http_urls = re.findall(r'http://[^"\'\s]+', content)
                for url in http_urls:
                    if 'localhost' not in url and '127.0.0.1' not in url:
                        insecure_communication.append(f"{file_path}: Insecure HTTP URL: {url}")
                
                # Check for deprecated TLS versions
                if re.search(r'tls.*1\.[01]|ssl.*[23]', content, re.IGNORECASE):
                    insecure_communication.append(f"{file_path}: Deprecated TLS/SSL version")
        
        # Assert
        if insecure_communication:
            pytest.fail(f"Insecure communication patterns found:\n" + "\n".join(insecure_communication))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])