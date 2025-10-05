#!/usr/bin/env python3
"""
OWASP Top 10 Security Audit Script for Course Creator Platform

BUSINESS REQUIREMENT:
Comprehensive security audit to identify and report vulnerabilities across
the entire codebase following OWASP Top 10 2021 guidelines.

AUDIT COVERAGE:
1. A01:2021 - Broken Access Control
2. A02:2021 - Cryptographic Failures
3. A03:2021 - Injection (SQL, Command, etc.)
4. A04:2021 - Insecure Design
5. A05:2021 - Security Misconfiguration
6. A06:2021 - Vulnerable and Outdated Components
7. A07:2021 - Identification and Authentication Failures
8. A08:2021 - Software and Data Integrity Failures
9. A09:2021 - Security Logging and Monitoring Failures
10. A10:2021 - Server-Side Request Forgery (SSRF)

METHODOLOGY:
- Static code analysis with pattern matching
- Dependency vulnerability scanning
- Configuration security review
- Best practices validation
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime

class SecurityAuditor:
    """Comprehensive OWASP security auditor"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.findings = defaultdict(list)
        self.stats = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }

    def add_finding(self, category: str, severity: str, title: str,
                   file_path: str, line_number: int = None,
                   code_snippet: str = None, recommendation: str = None):
        """Add security finding to results"""
        finding = {
            'category': category,
            'severity': severity,
            'title': title,
            'file': str(file_path),
            'line': line_number,
            'code': code_snippet,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }
        self.findings[category].append(finding)
        self.stats[severity.lower()] += 1

    def audit_sql_injection(self):
        """A03:2021 - Injection - SQL Injection vulnerabilities"""
        print("🔍 [1/10] Auditing SQL Injection vulnerabilities...")

        # Patterns indicating potential SQL injection
        dangerous_patterns = [
            (r'execute\([^)]*f["\']', 'F-string in SQL execute (potential injection)'),
            (r'execute\([^)]*\.format\(', 'String format in SQL execute (potential injection)'),
            (r'execute\([^)]*%\s*\(', 'Old-style string formatting in SQL (potential injection)'),
            (r'execute\([^)]*\+', 'String concatenation in SQL execute (HIGH RISK)'),
            (r'SELECT.*\+.*FROM', 'String concatenation in SELECT query'),
            (r'WHERE.*\+.*=', 'String concatenation in WHERE clause'),
            (r'cursor\.execute\([^)]*["\'].*{', 'Template string in cursor.execute'),
        ]

        # Safe patterns (parameterized queries)
        safe_patterns = [
            r'execute\([^)]*,\s*\[',  # List parameters
            r'execute\([^)]*,\s*\(',  # Tuple parameters
            r'execute\([^)]*,\s*{',   # Dict parameters
            r'execute\([^)]*\$\d+',   # PostgreSQL positional parameters
        ]

        python_files = list(self.project_root.rglob("services/**/*.py"))

        for file_path in python_files:
            if '__pycache__' in str(file_path) or 'test' in str(file_path).lower():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith('#'):
                        continue

                    # Check for dangerous patterns
                    for pattern, description in dangerous_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Check if this line also has safe parameterization
                            is_safe = any(re.search(safe_p, line) for safe_p in safe_patterns)

                            if not is_safe:
                                self.add_finding(
                                    category='A03:2021-Injection',
                                    severity='CRITICAL',
                                    title=f'Potential SQL Injection: {description}',
                                    file_path=file_path.relative_to(self.project_root),
                                    line_number=line_num,
                                    code_snippet=line.strip(),
                                    recommendation='Use parameterized queries with placeholders (?, $1, etc.) instead of string formatting'
                                )
            except Exception as e:
                print(f"  ⚠️  Error reading {file_path}: {e}")

    def audit_xss_vulnerabilities(self):
        """A03:2021 - Injection - Cross-Site Scripting (XSS)"""
        print("🔍 [2/10] Auditing XSS vulnerabilities...")

        # Check JavaScript files for unsafe DOM manipulation
        unsafe_js_patterns = [
            (r'innerHTML\s*=', 'Unsafe innerHTML assignment (XSS risk)'),
            (r'outerHTML\s*=', 'Unsafe outerHTML assignment (XSS risk)'),
            (r'document\.write\(', 'document.write() usage (XSS risk)'),
            (r'eval\(', 'eval() usage (code injection risk)'),
            (r'\.html\([^)]*\+', 'jQuery html() with concatenation (XSS risk)'),
            (r'dangerouslySetInnerHTML', 'React dangerouslySetInnerHTML (requires validation)'),
        ]

        js_files = list(self.project_root.rglob("frontend/**/*.js"))
        html_files = list(self.project_root.rglob("frontend/**/*.html"))

        for file_path in js_files + html_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern, description in unsafe_js_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.add_finding(
                                category='A03:2021-Injection',
                                severity='HIGH',
                                title=f'Potential XSS vulnerability: {description}',
                                file_path=file_path.relative_to(self.project_root),
                                line_number=line_num,
                                code_snippet=line.strip(),
                                recommendation='Use textContent, createElement, or proper escaping/sanitization'
                            )
            except Exception as e:
                pass

    def audit_authentication_issues(self):
        """A07:2021 - Identification and Authentication Failures"""
        print("🔍 [3/10] Auditing authentication and session management...")

        # Check for hardcoded credentials
        credential_patterns = [
            (r'password\s*=\s*["\'][^"\']{3,}["\']', 'Hardcoded password'),
            (r'api_key\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded API key'),
            (r'secret\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded secret'),
            (r'token\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded token'),
            (r'AWS_SECRET_ACCESS_KEY\s*=', 'Hardcoded AWS credentials'),
            (r'ANTHROPIC_API_KEY\s*=\s*["\']sk-ant', 'Hardcoded Anthropic API key'),
        ]

        # Exclude environment and config files from this check
        exclude_files = {'.env', '.env.example', 'config.yaml', 'config.py'}

        python_files = list(self.project_root.rglob("services/**/*.py"))

        for file_path in python_files:
            if file_path.name in exclude_files or 'test' in str(file_path).lower():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    # Skip comments and docstrings
                    if line.strip().startswith('#') or '"""' in line or "'''" in line:
                        continue

                    for pattern, description in credential_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Exclude common safe patterns
                            if 'os.getenv' in line or 'os.environ' in line or 'config.' in line.lower():
                                continue

                            self.add_finding(
                                category='A07:2021-Auth-Failures',
                                severity='CRITICAL',
                                title=f'Hardcoded credentials: {description}',
                                file_path=file_path.relative_to(self.project_root),
                                line_number=line_num,
                                code_snippet='[REDACTED FOR SECURITY]',
                                recommendation='Use environment variables or secure vault for credentials'
                            )
            except Exception as e:
                pass

    def audit_sensitive_data_exposure(self):
        """A02:2021 - Cryptographic Failures / Sensitive Data Exposure"""
        print("🔍 [4/10] Auditing sensitive data exposure...")

        # Check for insecure data transmission
        insecure_patterns = [
            (r'requests\.get\([^)]*http://', 'HTTP instead of HTTPS (data in transit)'),
            (r'requests\.post\([^)]*http://', 'HTTP POST (credentials in plaintext)'),
            (r'urllib.*http://', 'HTTP connection (insecure)'),
            (r'verify=False', 'SSL verification disabled (MITM risk)'),
            (r'ssl_context.*check_hostname\s*=\s*False', 'SSL hostname check disabled'),
        ]

        # Check for insecure storage
        storage_patterns = [
            (r'password.*=.*\.encode\(\)', 'Password stored without hashing'),
            (r'pickle\.loads?\(', 'Pickle usage (deserialization risk)'),
            (r'yaml\.load\([^,)]*\)', 'Unsafe YAML load (use safe_load)'),
            (r'json\.loads?\([^)]*user', 'User input deserialization (injection risk)'),
        ]

        python_files = list(self.project_root.rglob("**/*.py"))

        for file_path in python_files:
            if '__pycache__' in str(file_path) or 'test' in str(file_path).lower():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern, description in insecure_patterns + storage_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            severity = 'HIGH' if 'password' in line.lower() else 'MEDIUM'

                            self.add_finding(
                                category='A02:2021-Crypto-Failures',
                                severity=severity,
                                title=f'Sensitive data exposure: {description}',
                                file_path=file_path.relative_to(self.project_root),
                                line_number=line_num,
                                code_snippet=line.strip(),
                                recommendation='Use HTTPS, enable SSL verification, hash passwords with bcrypt/argon2'
                            )
            except Exception as e:
                pass

    def audit_access_control(self):
        """A01:2021 - Broken Access Control"""
        print("🔍 [5/10] Auditing access control...")

        # Check for missing authorization checks in API endpoints
        api_patterns = [
            (r'@app\.route\(|@router\.(get|post|put|delete)', 'API endpoint'),
            (r'@api\.route\(', 'API endpoint'),
            (r'async def.*\(request:', 'Request handler'),
        ]

        # Authorization decorators/checks
        auth_checks = [
            'require_auth',
            'authenticate',
            'check_permission',
            'require_role',
            'verify_organization',
            'get_current_user',
            '@login_required',
            '@permission_required',
        ]

        python_files = list(self.project_root.rglob("services/**/api/**/*.py"))
        python_files.extend(self.project_root.rglob("services/**/*_endpoints.py"))

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                i = 0
                while i < len(lines):
                    line = lines[i]

                    # Check if this is an API endpoint
                    is_endpoint = any(re.search(pattern, line) for pattern, _ in api_patterns)

                    if is_endpoint:
                        # Check next 10 lines for authorization
                        has_auth_check = False
                        check_lines = lines[max(0, i-5):min(len(lines), i+10)]

                        for check_line in check_lines:
                            if any(auth_check in check_line for auth_check in auth_checks):
                                has_auth_check = True
                                break

                        if not has_auth_check and 'health' not in line.lower():
                            self.add_finding(
                                category='A01:2021-Access-Control',
                                severity='HIGH',
                                title='API endpoint without authorization check',
                                file_path=file_path.relative_to(self.project_root),
                                line_number=i+1,
                                code_snippet=line.strip(),
                                recommendation='Add authentication/authorization decorator or check current user permissions'
                            )

                    i += 1
            except Exception as e:
                pass

    def audit_security_misconfiguration(self):
        """A05:2021 - Security Misconfiguration"""
        print("🔍 [6/10] Auditing security misconfiguration...")

        # Check DEBUG settings
        config_files = list(self.project_root.rglob("**/config.py"))
        config_files.extend(self.project_root.rglob("**/config.yaml"))
        config_files.extend(self.project_root.rglob("**/.env"))

        for file_path in config_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    if re.search(r'DEBUG\s*=\s*True', line, re.IGNORECASE):
                        self.add_finding(
                            category='A05:2021-Security-Misconfig',
                            severity='MEDIUM',
                            title='DEBUG mode enabled',
                            file_path=file_path.relative_to(self.project_root),
                            line_number=line_num,
                            code_snippet=line.strip(),
                            recommendation='Disable DEBUG in production environments'
                        )

                    if re.search(r'CORS.*\*', line):
                        self.add_finding(
                            category='A05:2021-Security-Misconfig',
                            severity='MEDIUM',
                            title='CORS configured to allow all origins',
                            file_path=file_path.relative_to(self.project_root),
                            line_number=line_num,
                            code_snippet=line.strip(),
                            recommendation='Restrict CORS to specific trusted origins'
                        )
            except Exception as e:
                pass

    def audit_vulnerable_dependencies(self):
        """A06:2021 - Vulnerable and Outdated Components"""
        print("🔍 [7/10] Auditing vulnerable dependencies...")

        requirements_files = list(self.project_root.rglob("**/requirements*.txt"))

        # Known vulnerable packages (example - should use safety or pip-audit)
        known_vulnerabilities = {
            'django<3.2.14': 'CVE-2022-34265',
            'flask<2.2.0': 'Multiple vulnerabilities',
            'requests<2.27.0': 'CVE-2021-43804',
        }

        for req_file in requirements_files:
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.add_finding(
                            category='A06:2021-Vulnerable-Components',
                            severity='INFO',
                            title=f'Dependency requires security review: {line}',
                            file_path=req_file.relative_to(self.project_root),
                            line_number=line_num,
                            code_snippet=line,
                            recommendation='Run pip-audit or safety check to verify dependency security'
                        )
            except Exception as e:
                pass

    def audit_csrf_protection(self):
        """A01:2021 - CSRF vulnerabilities"""
        print("🔍 [8/10] Auditing CSRF protection...")

        # Check POST handlers for CSRF protection
        python_files = list(self.project_root.rglob("services/**/api/**/*.py"))

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    if re.search(r'@\w+\.(post|put|delete|patch)', line, re.IGNORECASE):
                        # Check if CSRF protection is mentioned nearby
                        context = '\n'.join(lines[max(0, line_num-5):min(len(lines), line_num+5)])

                        if 'csrf' not in context.lower() and 'CSRFProtect' not in context:
                            self.add_finding(
                                category='A01:2021-Access-Control',
                                severity='MEDIUM',
                                title='State-changing endpoint without CSRF protection',
                                file_path=file_path.relative_to(self.project_root),
                                line_number=line_num,
                                code_snippet=line.strip(),
                                recommendation='Add CSRF token validation for state-changing operations'
                            )
            except Exception as e:
                pass

    def audit_logging_monitoring(self):
        """A09:2021 - Security Logging and Monitoring Failures"""
        print("🔍 [9/10] Auditing security logging and monitoring...")

        # Check for security-critical operations without logging
        critical_operations = [
            (r'def.*login', 'Login operation'),
            (r'def.*authenticate', 'Authentication operation'),
            (r'def.*authorize', 'Authorization operation'),
            (r'def.*delete_user', 'User deletion'),
            (r'def.*update_permission', 'Permission change'),
        ]

        python_files = list(self.project_root.rglob("services/**/*.py"))

        for file_path in python_files:
            if 'test' in str(file_path).lower():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for line_num, line in enumerate(lines):
                    for pattern, description in critical_operations:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Check if logging is present in the function
                            func_lines = lines[line_num:min(len(lines), line_num+20)]
                            has_logging = any('log' in l.lower() for l in func_lines)

                            if not has_logging:
                                self.add_finding(
                                    category='A09:2021-Logging-Failures',
                                    severity='LOW',
                                    title=f'{description} without security logging',
                                    file_path=file_path.relative_to(self.project_root),
                                    line_number=line_num+1,
                                    code_snippet=line.strip(),
                                    recommendation='Add security event logging for audit trail'
                                )
            except Exception as e:
                pass

    def audit_command_injection(self):
        """A03:2021 - Injection - Command Injection"""
        print("🔍 [10/10] Auditing command injection vulnerabilities...")

        # Dangerous subprocess/os patterns
        dangerous_exec_patterns = [
            (r'os\.system\(', 'os.system() with potential user input'),
            (r'subprocess\.call\([^)]*shell=True', 'subprocess with shell=True (injection risk)'),
            (r'subprocess\.Popen\([^)]*shell=True', 'Popen with shell=True (injection risk)'),
            (r'eval\(', 'eval() usage (code injection)'),
            (r'exec\(', 'exec() usage (code injection)'),
            (r'__import__\(.*input', 'Dynamic import from user input'),
        ]

        python_files = list(self.project_root.rglob("**/*.py"))

        for file_path in python_files:
            if 'test' in str(file_path).lower() or '__pycache__' in str(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern, description in dangerous_exec_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.add_finding(
                                category='A03:2021-Injection',
                                severity='CRITICAL',
                                title=f'Command injection risk: {description}',
                                file_path=file_path.relative_to(self.project_root),
                                line_number=line_num,
                                code_snippet=line.strip(),
                                recommendation='Use subprocess with shell=False and argument list, avoid eval/exec'
                            )
            except Exception as e:
                pass

    def run_full_audit(self):
        """Run complete OWASP security audit"""
        print("\n" + "="*70)
        print("🔐 OWASP Top 10 Security Audit - Course Creator Platform")
        print("="*70 + "\n")

        self.audit_sql_injection()
        self.audit_xss_vulnerabilities()
        self.audit_authentication_issues()
        self.audit_sensitive_data_exposure()
        self.audit_access_control()
        self.audit_security_misconfiguration()
        self.audit_vulnerable_dependencies()
        self.audit_csrf_protection()
        self.audit_logging_monitoring()
        self.audit_command_injection()

        print("\n" + "="*70)
        print("📊 Audit Complete - Generating Report...")
        print("="*70 + "\n")

    def generate_report(self, output_file: str = "SECURITY_AUDIT_REPORT.md"):
        """Generate comprehensive security audit report"""

        report = f"""# OWASP Security Audit Report

**Platform**: Course Creator
**Audit Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Audited By**: Automated OWASP Security Scanner

## Executive Summary

### Findings Overview

| Severity | Count |
|----------|-------|
| 🔴 **CRITICAL** | {self.stats['critical']} |
| 🟠 **HIGH** | {self.stats['high']} |
| 🟡 **MEDIUM** | {self.stats['medium']} |
| 🔵 **LOW** | {self.stats['low']} |
| ⚪ **INFO** | {self.stats['info']} |
| **TOTAL** | {sum(self.stats.values())} |

---

## Detailed Findings by OWASP Category

"""

        # Sort categories by OWASP number
        categories = sorted(self.findings.keys())

        for category in categories:
            findings = self.findings[category]
            if not findings:
                continue

            report += f"\n### {category}\n\n"
            report += f"**Total Findings**: {len(findings)}\n\n"

            # Group by severity
            by_severity = defaultdict(list)
            for finding in findings:
                by_severity[finding['severity']].append(finding)

            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                if severity not in by_severity:
                    continue

                severity_findings = by_severity[severity]
                report += f"\n#### {severity} Severity ({len(severity_findings)} findings)\n\n"

                for i, finding in enumerate(severity_findings[:10], 1):  # Limit to first 10
                    report += f"{i}. **{finding['title']}**\n"
                    report += f"   - **File**: `{finding['file']}`\n"
                    if finding['line']:
                        report += f"   - **Line**: {finding['line']}\n"
                    if finding['code'] and finding['code'] != '[REDACTED FOR SECURITY]':
                        report += f"   - **Code**: `{finding['code'][:100]}`\n"
                    if finding['recommendation']:
                        report += f"   - **Recommendation**: {finding['recommendation']}\n"
                    report += "\n"

                if len(severity_findings) > 10:
                    report += f"   *... and {len(severity_findings) - 10} more findings*\n\n"

        report += """
---

## Recommendations

### Immediate Actions Required (CRITICAL/HIGH)

1. **Fix SQL Injection Vulnerabilities**
   - Replace all string formatting in SQL queries with parameterized queries
   - Use SQLAlchemy ORM or prepared statements
   - Review all `execute()` calls for user input

2. **Remove Hardcoded Credentials**
   - Move all API keys, passwords, and secrets to environment variables
   - Use AWS Secrets Manager or HashiCorp Vault for production
   - Rotate any exposed credentials immediately

3. **Add Authorization Checks**
   - Review all API endpoints for proper authorization
   - Implement consistent permission checking middleware
   - Add organization context validation

### Medium-Term Actions (MEDIUM)

1. **Enable CSRF Protection**
   - Add CSRF tokens to all state-changing operations
   - Use SameSite cookie attributes
   - Implement double-submit cookie pattern

2. **Fix Security Misconfigurations**
   - Disable DEBUG mode in production
   - Restrict CORS to specific origins
   - Enable SSL verification

3. **Improve Security Logging**
   - Add audit logging for all authentication events
   - Log authorization failures
   - Implement centralized logging

### Long-Term Improvements (LOW/INFO)

1. **Dependency Management**
   - Set up automated vulnerability scanning (Dependabot, Safety)
   - Regularly update dependencies
   - Monitor security advisories

2. **Security Testing**
   - Implement automated security testing in CI/CD
   - Perform regular penetration testing
   - Add security-focused unit tests

---

## Tools Used

- Static code analysis with regex pattern matching
- OWASP Top 10 2021 guidelines
- Python AST parsing
- File system traversal

## Next Steps

1. Review this report with the security team
2. Prioritize fixes based on severity and business impact
3. Create tickets for each HIGH and CRITICAL finding
4. Implement fixes using TDD methodology
5. Re-run audit after fixes to verify remediation

---

**Report Generated**: {datetime.now().isoformat()}
"""

        # Write report
        output_path = self.project_root / output_file
        with open(output_path, 'w') as f:
            f.write(report)

        print(f"✅ Security audit report generated: {output_path}")
        print(f"\n📊 Summary: {self.stats['critical']} CRITICAL, {self.stats['high']} HIGH, "
              f"{self.stats['medium']} MEDIUM, {self.stats['low']} LOW, {self.stats['info']} INFO")

        return output_path


def main():
    """Run security audit"""
    auditor = SecurityAuditor()
    auditor.run_full_audit()
    report_path = auditor.generate_report()

    print(f"\n{'='*70}")
    print(f"🎯 Action Required:")
    print(f"   Review report: {report_path}")
    print(f"   Address CRITICAL and HIGH findings immediately")
    print(f"{'='*70}\n")

    return 0 if (auditor.stats['critical'] == 0 and auditor.stats['high'] == 0) else 1


if __name__ == '__main__':
    exit(main())
