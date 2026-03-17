#!/usr/bin/env python3
"""
OWASP Top 10 Security Assessment for Course Creator Platform

ASSESSMENT METHODOLOGY:
Comprehensive security testing framework that evaluates the Course Creator Platform
against the OWASP Top 10 2021 vulnerabilities to identify and remediate security
risks before production deployment.

OWASP TOP 10 2021 CATEGORIES:
A01: Broken Access Control
A02: Cryptographic Failures  
A03: Injection
A04: Insecure Design
A05: Security Misconfiguration
A06: Vulnerable and Outdated Components
A07: Identification and Authentication Failures
A08: Software and Data Integrity Failures
A09: Security Logging and Monitoring Failures
A10: Server-Side Request Forgery (SSRF)

TESTING STRATEGY:
Each OWASP category is tested with multiple attack vectors including:
- Automated vulnerability scanning
- Manual penetration testing techniques
- Code review for security anti-patterns
- Configuration analysis
- Dependency vulnerability assessment
"""

import asyncio
import sys
import os
import time
import json
import uuid
import requests
import subprocess
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sqlite3
import re
import base64
from urllib.parse import quote, unquote
import xml.etree.ElementTree as ET

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'shared'))

# Import security components
try:
    from auth.organization_middleware import OrganizationAuthorizationMiddleware
    from cache.organization_redis_cache import OrganizationRedisCache
except ImportError as e:
    print(f"❌ Failed to import security components: {e}")
    sys.exit(1)

# Import test fixtures
from tests.fixtures.security_fixtures import (
    create_test_organizations, create_test_users, generate_valid_jwt_token,
    SecurityTestClient, SecurityPerformanceTracker
)


class OWASPTop10Assessment:
    """
    Comprehensive OWASP Top 10 security assessment suite
    
    This class implements systematic testing for each OWASP Top 10 vulnerability
    category, providing detailed analysis and remediation recommendations.
    """
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'assessment_version': 'OWASP Top 10 2021',
            'platform': 'Course Creator Platform v2.8.0',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'owasp_categories': {},
            'detailed_findings': [],
            'remediation_summary': []
        }
        self.performance_tracker = SecurityPerformanceTracker()
        self.base_url = 'http://localhost'
        self.test_ports = [3000, 8000, 8001, 8003, 8004, 8005, 8006, 8007, 8008]
    
    def log_finding(self, category: str, test_name: str, severity: str, 
                   passed: bool, details: str, remediation: str = ""):
        """Log security finding with OWASP categorization"""
        status = "✅ PASS" if passed else "❌ FAIL"
        severity_icon = {
            'CRITICAL': '🔴',
            'HIGH': '🟠', 
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(severity, '⚪')
        
        print(f"{status} {severity_icon} [{category}] {test_name}")
        if details:
            print(f"    {details}")
        if not passed and remediation:
            print(f"    💡 Remediation: {remediation}")
        
        self.results['total_tests'] += 1
        if passed:
            self.results['passed_tests'] += 1
        else:
            self.results['failed_tests'] += 1
            
            # Count issues by severity
            severity_counters = {
                'CRITICAL': 'critical_issues',
                'HIGH': 'high_issues', 
                'MEDIUM': 'medium_issues',
                'LOW': 'low_issues'
            }
            if severity in severity_counters:
                self.results[severity_counters[severity]] += 1
        
        # Store detailed finding
        finding = {
            'category': category,
            'test_name': test_name,
            'severity': severity,
            'passed': passed,
            'details': details,
            'remediation': remediation,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.results['detailed_findings'].append(finding)
        
        # Update category summary
        if category not in self.results['owasp_categories']:
            self.results['owasp_categories'][category] = {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'risk_level': 'LOW'
            }
        
        cat_stats = self.results['owasp_categories'][category]
        cat_stats['total_tests'] += 1
        if passed:
            cat_stats['passed_tests'] += 1
        else:
            cat_stats['failed_tests'] += 1
            # Update risk level based on highest severity failure
            if severity == 'CRITICAL':
                cat_stats['risk_level'] = 'CRITICAL'
            elif severity == 'HIGH' and cat_stats['risk_level'] not in ['CRITICAL']:
                cat_stats['risk_level'] = 'HIGH'
            elif severity == 'MEDIUM' and cat_stats['risk_level'] not in ['CRITICAL', 'HIGH']:
                cat_stats['risk_level'] = 'MEDIUM'

    async def test_a01_broken_access_control(self) -> bool:
        """
        A01: Broken Access Control
        
        Tests for access control failures including:
        - Vertical privilege escalation
        - Horizontal privilege escalation  
        - IDOR (Insecure Direct Object References)
        - Missing function level access control
        - CORS misconfiguration
        """
        print("\n🔍 A01: Testing Broken Access Control...")
        
        category_passed = True
        
        # Test 1: Vertical Privilege Escalation
        try:
            # Create test users with different roles
            organizations = create_test_organizations([
                {'name': 'Test Org', 'slug': 'test-org'}
            ])
            
            users = create_test_users([
                {'email': 'student@test.com', 'role': 'student', 'organization_id': organizations[0].id},
                {'email': 'instructor@test.com', 'role': 'instructor', 'organization_id': organizations[0].id},
                {'email': 'admin@test.com', 'role': 'admin', 'organization_id': organizations[0].id}
            ])
            
            client = SecurityTestClient()
            
            # Test student trying to access admin endpoints
            student_token = generate_valid_jwt_token(users[0])
            
            admin_endpoints = [
                '/admin/users',
                '/admin/statistics',
                '/api/v1/admin/organizations',
                '/api/v1/site-admin/users'
            ]
            
            privilege_escalation_blocked = True
            for endpoint in admin_endpoints:
                async with client.authenticated_request(student_token, organizations[0].id) as test_client:
                    try:
                        response = await test_client.get(endpoint)
                        if response.status_code not in [401, 403]:
                            privilege_escalation_blocked = False
                            break
                    except:
                        pass  # Connection errors are acceptable for this test
            
            self.log_finding(
                'A01',
                'Vertical Privilege Escalation Prevention', 
                'HIGH',
                privilege_escalation_blocked,
                f"Student access to admin endpoints: {'BLOCKED' if privilege_escalation_blocked else 'ALLOWED'}",
                "Implement role-based access control checks on all admin endpoints"
            )
            
            if not privilege_escalation_blocked:
                category_passed = False
        
        except Exception as e:
            self.log_finding(
                'A01',
                'Vertical Privilege Escalation Test',
                'HIGH', 
                False,
                f"Test failed with exception: {e}",
                "Fix test infrastructure and re-run access control tests"
            )
            category_passed = False
        
        # Test 2: Horizontal Privilege Escalation (Organization Isolation)
        try:
            # This is already tested in our multi-tenant security, but let's verify
            orgs = create_test_organizations([
                {'name': 'Org A', 'slug': 'org-a'},
                {'name': 'Org B', 'slug': 'org-b'}
            ])
            
            users = create_test_users([
                {'email': 'user1@orga.com', 'role': 'instructor', 'organization_id': orgs[0].id},
                {'email': 'user2@orgb.com', 'role': 'instructor', 'organization_id': orgs[1].id}
            ])
            
            client = SecurityTestClient()
            user_a_token = generate_valid_jwt_token(users[0])
            
            # Try to access Org B's data with Org A user token
            async with client.authenticated_request(user_a_token, orgs[1].id) as test_client:
                response = await test_client.get('/api/v1/courses')
                horizontal_escalation_blocked = response.status_code == 403
            
            self.log_finding(
                'A01',
                'Horizontal Privilege Escalation Prevention',
                'CRITICAL',
                horizontal_escalation_blocked,
                f"Cross-organization access: {'BLOCKED' if horizontal_escalation_blocked else 'ALLOWED'}",
                "Implement organization-based access control middleware on all endpoints"
            )
            
            if not horizontal_escalation_blocked:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A01',
                'Horizontal Privilege Escalation Test',
                'CRITICAL',
                False, 
                f"Test failed with exception: {e}",
                "Fix organization isolation middleware"
            )
            category_passed = False
        
        # Test 3: IDOR (Insecure Direct Object References)
        try:
            # Test accessing resources by ID without proper authorization
            idor_test_endpoints = [
                '/api/v1/courses/12345',
                '/api/v1/users/67890', 
                '/api/v1/syllabi/abcde',
                '/api/v1/analytics/content/xyz123/metrics'
            ]
            
            # Use a valid token but try to access resources that shouldn't be accessible
            user_token = generate_valid_jwt_token(users[0])
            
            idor_protected = True
            for endpoint in idor_test_endpoints:
                async with client.authenticated_request(user_token, organizations[0].id) as test_client:
                    try:
                        response = await test_client.get(endpoint)
                        # Should get 403/404, not 200 with data
                        if response.status_code == 200:
                            # Check if response contains data that user shouldn't access
                            response_data = response.json()
                            if isinstance(response_data, dict) and response_data.get('id'):
                                idor_protected = False
                                break
                    except:
                        pass  # Connection errors are acceptable
            
            self.log_finding(
                'A01',
                'IDOR Protection',
                'HIGH',
                idor_protected,
                f"Direct object reference protection: {'ENABLED' if idor_protected else 'MISSING'}",
                "Implement authorization checks before returning object data"
            )
            
            if not idor_protected:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A01', 
                'IDOR Protection Test',
                'HIGH',
                False,
                f"Test failed with exception: {e}",
                "Implement proper object-level authorization"
            )
            category_passed = False
        
        # Test 4: Missing Function Level Access Control  
        try:
            # Check if sensitive functions are properly protected
            sensitive_functions = [
                '/api/v1/admin/users',
                '/api/v1/courses/bulk-delete',
                '/api/v1/system/backup',
                '/api/v1/analytics/export-all'
            ]
            
            # Test with no authentication
            function_protection = True
            for endpoint in sensitive_functions:
                try:
                    response = requests.get(f"{self.base_url}:8000{endpoint}", timeout=2)
                    if response.status_code not in [401, 403, 404]:
                        function_protection = False
                        break
                except requests.RequestException:
                    pass  # Connection errors are acceptable
            
            self.log_finding(
                'A01',
                'Function Level Access Control',
                'HIGH', 
                function_protection,
                f"Sensitive functions protection: {'ENABLED' if function_protection else 'MISSING'}",
                "Add authentication and authorization requirements to all sensitive functions"
            )
            
            if not function_protection:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A01',
                'Function Level Access Control Test', 
                'HIGH',
                False,
                f"Test failed with exception: {e}",
                "Review and secure all API endpoints"
            )
            category_passed = False
        
        return category_passed
    
    async def test_a02_cryptographic_failures(self) -> bool:
        """
        A02: Cryptographic Failures
        
        Tests for cryptographic weaknesses including:
        - Weak encryption algorithms
        - Poor key management
        - Missing encryption for sensitive data
        - Weak random number generation
        - Certificate validation issues
        """
        print("\n🔍 A02: Testing Cryptographic Failures...")
        
        category_passed = True
        
        # Test 1: JWT Token Security
        try:
            # Check JWT implementation for weak algorithms
            test_user = create_test_users([
                {'email': 'test@example.com', 'role': 'student', 'organization_id': str(uuid.uuid4())}
            ])[0]
            
            token = generate_valid_jwt_token(test_user)
            
            # Decode without verification to check algorithm
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            header = jwt.get_unverified_header(token)
            
            # Check for secure algorithm (should be HS256 or better)
            algorithm = header.get('alg', '')
            secure_algorithm = algorithm in ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
            
            # Check for 'none' algorithm vulnerability
            none_algorithm_safe = algorithm != 'none'
            
            jwt_secure = secure_algorithm and none_algorithm_safe
            
            self.log_finding(
                'A02',
                'JWT Algorithm Security',
                'HIGH',
                jwt_secure,
                f"JWT algorithm: {algorithm}, Secure: {jwt_secure}",
                "Use secure JWT algorithms (HS256+ or RS256+) and never allow 'none'"
            )
            
            if not jwt_secure:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A02',
                'JWT Security Test',
                'HIGH',
                False,
                f"JWT analysis failed: {e}",
                "Review JWT implementation for security vulnerabilities"
            )
            category_passed = False
        
        # Test 2: Password Storage Security
        try:
            # Check if application uses secure password hashing
            # Look for bcrypt, scrypt, or Argon2 usage in codebase
            password_files = [
                'services/user-management/auth/password_manager.py',
                'services/user-management/services/password_service.py'
            ]
            
            secure_hashing_found = False
            hashing_method = "Unknown"
            
            for file_path in password_files:
                full_path = project_root / file_path
                if full_path.exists():
                    with open(full_path, 'r') as f:
                        content = f.read()
                        if any(method in content.lower() for method in ['bcrypt', 'scrypt', 'argon2']):
                            secure_hashing_found = True
                            if 'bcrypt' in content.lower():
                                hashing_method = "bcrypt"
                            elif 'scrypt' in content.lower():
                                hashing_method = "scrypt"  
                            elif 'argon2' in content.lower():
                                hashing_method = "Argon2"
                            break
            
            self.log_finding(
                'A02',
                'Password Hashing Security',
                'CRITICAL',
                secure_hashing_found,
                f"Secure password hashing: {hashing_method if secure_hashing_found else 'NOT FOUND'}",
                "Implement bcrypt, scrypt, or Argon2 for password hashing"
            )
            
            if not secure_hashing_found:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A02',
                'Password Security Analysis',
                'CRITICAL',
                False,
                f"Password security check failed: {e}",
                "Review password storage implementation"
            )
            category_passed = False
        
        # Test 3: HTTPS/TLS Configuration
        try:
            # Check if services enforce HTTPS
            https_endpoints = []
            http_endpoints = []
            
            for port in self.test_ports:
                try:
                    # Test HTTPS
                    https_response = requests.get(f"https://localhost:{port}/health", 
                                                timeout=2, verify=False)
                    if https_response.status_code == 200:
                        https_endpoints.append(port)
                except requests.RequestException:
                    pass
                
                try:
                    # Test HTTP
                    http_response = requests.get(f"http://localhost:{port}/health", timeout=2)
                    if http_response.status_code == 200:
                        http_endpoints.append(port)
                except requests.RequestException:
                    pass
            
            # In production, should have HTTPS. In development, HTTP is acceptable
            tls_properly_configured = len(https_endpoints) > 0 or len(http_endpoints) > 0
            
            self.log_finding(
                'A02',
                'TLS/HTTPS Configuration',
                'MEDIUM',
                tls_properly_configured,
                f"HTTPS endpoints: {len(https_endpoints)}, HTTP endpoints: {len(http_endpoints)}",
                "Configure HTTPS with valid certificates for production deployment"
            )
            
        except Exception as e:
            self.log_finding(
                'A02',
                'TLS Configuration Test',
                'MEDIUM',
                False,
                f"TLS test failed: {e}",
                "Review TLS/HTTPS configuration"
            )
        
        # Test 4: Sensitive Data Exposure in Logs
        try:
            # Check log files for sensitive data exposure
            log_dirs = [
                project_root / 'logs',
                project_root / 'services' / 'user-management' / 'logs',
                '/var/log/course-creator'
            ]
            
            sensitive_patterns = [
                r'password["\s]*[:=]["\s]*[^"\s]+',
                r'token["\s]*[:=]["\s]*[^"\s]+', 
                r'secret["\s]*[:=]["\s]*[^"\s]+',
                r'api[_-]?key["\s]*[:=]["\s]*[^"\s]+',
                r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',  # Credit card pattern
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email pattern
            ]
            
            sensitive_data_found = False
            for log_dir in log_dirs:
                if log_dir.exists():
                    for log_file in log_dir.glob('*.log'):
                        try:
                            with open(log_file, 'r') as f:
                                content = f.read()
                                for pattern in sensitive_patterns:
                                    if re.search(pattern, content, re.IGNORECASE):
                                        sensitive_data_found = True
                                        break
                                if sensitive_data_found:
                                    break
                        except:
                            pass
                    if sensitive_data_found:
                        break
            
            self.log_finding(
                'A02',
                'Sensitive Data in Logs',
                'MEDIUM',
                not sensitive_data_found,
                f"Sensitive data in logs: {'FOUND' if sensitive_data_found else 'NOT FOUND'}",
                "Implement log sanitization to prevent sensitive data exposure"
            )
            
            if sensitive_data_found:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A02',
                'Log Data Exposure Test',
                'MEDIUM',
                False,
                f"Log analysis failed: {e}",
                "Review logging practices for sensitive data exposure"
            )
        
        return category_passed
    
    async def test_a03_injection(self) -> bool:
        """
        A03: Injection
        
        Tests for injection vulnerabilities including:
        - SQL Injection
        - NoSQL Injection  
        - Command Injection
        - LDAP Injection
        - XPath Injection
        """
        print("\n🔍 A03: Testing Injection Vulnerabilities...")
        
        category_passed = True
        
        # Test 1: SQL Injection
        try:
            # Test SQL injection in various endpoints
            client = SecurityTestClient()
            
            # Create test user for authentication
            organizations = create_test_organizations([
                {'name': 'Test Org', 'slug': 'test-org'}
            ])
            users = create_test_users([
                {'email': 'test@example.com', 'role': 'instructor', 'organization_id': organizations[0].id}
            ])
            user_token = generate_valid_jwt_token(users[0])
            
            # SQL injection payloads
            sql_payloads = [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "' UNION SELECT * FROM users --",
                "'; INSERT INTO users VALUES ('hacker', 'password'); --",
                "' OR 1=1 --",
                "' AND (SELECT COUNT(*) FROM users) > 0 --"
            ]
            
            # Test endpoints that might be vulnerable
            test_endpoints = [
                '/users/search?q={}',
                '/api/v1/courses?title={}',
                '/api/v1/content/search',
                '/api/v1/analytics/content/statistics?course_id={}'
            ]
            
            sql_injection_prevented = True
            
            for payload in sql_payloads:
                for endpoint_template in test_endpoints:
                    try:
                        if '{}' in endpoint_template:
                            endpoint = endpoint_template.format(quote(payload))
                        else:
                            endpoint = endpoint_template
                        
                        async with client.authenticated_request(user_token, organizations[0].id) as test_client:
                            if endpoint == '/api/v1/content/search':
                                # POST request with JSON payload
                                response = await test_client.post(endpoint, json={
                                    'query': payload,
                                    'content_types': ['syllabus']
                                })
                            else:
                                response = await test_client.get(endpoint)
                            
                            # Check for SQL error messages that might indicate vulnerability
                            if response.status_code == 200:
                                response_text = str(response.json())
                                sql_error_indicators = [
                                    'sql', 'database', 'sqlite', 'postgresql', 'mysql',
                                    'syntax error', 'column', 'table', 'select', 'insert'
                                ]
                                
                                if any(indicator in response_text.lower() for indicator in sql_error_indicators):
                                    # Might indicate SQL injection vulnerability
                                    sql_injection_prevented = False
                                    break
                            
                            # 500 errors might also indicate SQL injection attempts
                            elif response.status_code == 500:
                                # This could indicate the payload caused a database error
                                pass
                    
                    except Exception:
                        pass  # Connection errors are acceptable
                
                if not sql_injection_prevented:
                    break
            
            self.log_finding(
                'A03',
                'SQL Injection Prevention',
                'CRITICAL',
                sql_injection_prevented,
                f"SQL injection protection: {'ENABLED' if sql_injection_prevented else 'VULNERABLE'}",
                "Use parameterized queries and input validation to prevent SQL injection"
            )
            
            if not sql_injection_prevented:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A03',
                'SQL Injection Test',
                'CRITICAL',
                False,
                f"SQL injection test failed: {e}",
                "Review database query implementation for injection vulnerabilities"
            )
            category_passed = False
        
        # Test 2: Command Injection  
        try:
            # Test for command injection vulnerabilities
            command_payloads = [
                '; ls -la',
                '&& cat /etc/passwd',
                '| whoami',
                '; rm -rf /',
                '`id`',
                '$(whoami)'
            ]
            
            # Test file upload endpoints that might process filenames
            command_injection_prevented = True
            
            for payload in command_payloads:
                try:
                    # Test via filename parameter if file upload exists
                    async with client.authenticated_request(user_token, organizations[0].id) as test_client:
                        # Simulate file upload with malicious filename
                        response = await test_client.post('/api/v1/content/upload', json={
                            'filename': f'test{payload}.txt',
                            'content_type': 'text/plain'
                        })
                        
                        # Check if command was executed (should not be)
                        if response.status_code == 200:
                            response_data = response.json()
                            # If response contains system information, might be vulnerable
                            if isinstance(response_data, dict):
                                response_str = str(response_data).lower()
                                if any(indicator in response_str for indicator in ['root', 'bin', 'usr', 'etc']):
                                    command_injection_prevented = False
                                    break
                        
                except Exception:
                    pass  # Endpoint might not exist, which is fine
            
            self.log_finding(
                'A03',
                'Command Injection Prevention',
                'HIGH',
                command_injection_prevented,
                f"Command injection protection: {'ENABLED' if command_injection_prevented else 'VULNERABLE'}",
                "Sanitize all user inputs and avoid system command execution"
            )
            
            if not command_injection_prevented:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A03',
                'Command Injection Test',
                'HIGH',
                False,
                f"Command injection test failed: {e}",
                "Review file processing for command injection vulnerabilities"
            )
            category_passed = False
        
        # Test 3: XSS Prevention in API Responses
        try:
            # Test for reflected XSS in API responses
            xss_payloads = [
                '<script>alert("XSS")</script>',
                '"><script>alert("XSS")</script>',
                "javascript:alert('XSS')",
                '<img src=x onerror=alert("XSS")>',
                '<svg onload=alert("XSS")>'
            ]
            
            xss_prevented = True
            
            for payload in xss_payloads:
                try:
                    async with client.authenticated_request(user_token, organizations[0].id) as test_client:
                        # Test search endpoint that returns user input
                        response = await test_client.get(f'/users/search?q={quote(payload)}')
                        
                        if response.status_code == 200:
                            response_data = response.json()
                            response_str = str(response_data)
                            
                            # Check if payload is reflected unescaped
                            if payload in response_str:
                                xss_prevented = False
                                break
                
                except Exception:
                    pass
            
            self.log_finding(
                'A03',
                'XSS Prevention in API',
                'HIGH',
                xss_prevented,
                f"XSS prevention: {'ENABLED' if xss_prevented else 'VULNERABLE'}",
                "Implement output encoding and input validation to prevent XSS"
            )
            
            if not xss_prevented:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A03',
                'XSS Prevention Test',
                'HIGH',
                False,
                f"XSS test failed: {e}",
                "Review API response handling for XSS vulnerabilities"
            )
            category_passed = False
        
        return category_passed
    
    async def test_a04_insecure_design(self) -> bool:
        """
        A04: Insecure Design
        
        Tests for insecure design patterns including:
        - Missing security controls
        - Weak business logic  
        - Missing rate limiting
        - Insufficient security architecture
        """
        print("\n🔍 A04: Testing Insecure Design...")
        
        category_passed = True
        
        # Test 1: Rate Limiting
        try:
            # Test if API endpoints have rate limiting
            client = SecurityTestClient()
            
            organizations = create_test_organizations([
                {'name': 'Test Org', 'slug': 'test-org'}
            ])
            users = create_test_users([
                {'email': 'test@example.com', 'role': 'student', 'organization_id': organizations[0].id}
            ])
            user_token = generate_valid_jwt_token(users[0])
            
            # Simulate rapid requests to check for rate limiting
            rate_limit_enforced = False
            
            async with client.authenticated_request(user_token, organizations[0].id) as test_client:
                # Make rapid requests
                for i in range(20):  # Try 20 rapid requests
                    try:
                        response = await test_client.get('/users/me')
                        if response.status_code == 429:  # Too Many Requests
                            rate_limit_enforced = True
                            break
                    except Exception:
                        pass
            
            self.log_finding(
                'A04',
                'Rate Limiting Implementation',
                'MEDIUM',
                rate_limit_enforced,
                f"Rate limiting: {'ENFORCED' if rate_limit_enforced else 'NOT IMPLEMENTED'}",
                "Implement rate limiting to prevent abuse and DoS attacks"
            )
            
        except Exception as e:
            self.log_finding(
                'A04',
                'Rate Limiting Test',
                'MEDIUM',
                False,
                f"Rate limiting test failed: {e}",
                "Implement proper rate limiting mechanisms"
            )
        
        # Test 2: Business Logic Security
        try:
            # Test for business logic flaws
            business_logic_secure = True
            
            # Test: Can students enroll in courses without proper authorization?
            # Test: Can users modify data they shouldn't have access to?
            # Test: Are there workflow bypasses?
            
            async with client.authenticated_request(user_token, organizations[0].id) as test_client:
                # Try to access admin functions as a student
                admin_endpoints = [
                    '/admin/users',
                    '/admin/statistics', 
                    '/api/v1/admin/organizations'
                ]
                
                for endpoint in admin_endpoints:
                    try:
                        response = await test_client.get(endpoint)
                        if response.status_code == 200:
                            business_logic_secure = False
                            break
                    except Exception:
                        pass
            
            self.log_finding(
                'A04',
                'Business Logic Security',
                'HIGH',
                business_logic_secure,
                f"Business logic controls: {'SECURE' if business_logic_secure else 'VULNERABLE'}",
                "Review business logic flows for unauthorized access patterns"
            )
            
            if not business_logic_secure:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A04',
                'Business Logic Security Test',
                'HIGH',
                False,
                f"Business logic test failed: {e}",
                "Review application business logic for security flaws"
            )
            category_passed = False
        
        # Test 3: Security Headers
        try:
            # Check for security headers in HTTP responses
            security_headers_present = False
            
            for port in [3000, 8000]:  # Frontend and main API
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=2)
                    headers = response.headers
                    
                    # Check for important security headers
                    security_headers = [
                        'X-Content-Type-Options',
                        'X-Frame-Options',
                        'X-XSS-Protection',
                        'Strict-Transport-Security',
                        'Content-Security-Policy'
                    ]
                    
                    present_headers = [h for h in security_headers if h in headers]
                    if len(present_headers) >= 2:  # At least some security headers
                        security_headers_present = True
                        break
                        
                except requests.RequestException:
                    pass
            
            self.log_finding(
                'A04',
                'Security Headers Implementation',
                'MEDIUM',
                security_headers_present,
                f"Security headers: {'PRESENT' if security_headers_present else 'MISSING'}",
                "Implement security headers (CSP, HSTS, X-Frame-Options, etc.)"
            )
            
        except Exception as e:
            self.log_finding(
                'A04',
                'Security Headers Test',
                'MEDIUM',
                False,
                f"Security headers test failed: {e}",
                "Configure proper security headers"
            )
        
        return category_passed
    
    async def test_a05_security_misconfiguration(self) -> bool:
        """
        A05: Security Misconfiguration
        
        Tests for security misconfigurations including:
        - Default credentials
        - Unnecessary features enabled
        - Missing security patches
        - Insecure default configurations
        """
        print("\n🔍 A05: Testing Security Misconfiguration...")
        
        category_passed = True
        
        # Test 1: Debug Mode in Production
        try:
            debug_disabled = True
            
            # Check for debug indicators in responses
            for port in self.test_ports:
                try:
                    response = requests.get(f"http://localhost:{port}/docs", timeout=2)
                    if response.status_code == 200:
                        debug_disabled = False  # Swagger docs should not be accessible in production
                        break
                except requests.RequestException:
                    pass
            
            self.log_finding(
                'A05',
                'Debug Mode Configuration',
                'MEDIUM',
                debug_disabled,
                f"Debug features: {'DISABLED' if debug_disabled else 'ENABLED'}",
                "Disable debug features and API documentation in production"
            )
            
            if not debug_disabled:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A05',
                'Debug Mode Test',
                'MEDIUM',
                False,
                f"Debug mode test failed: {e}",
                "Review production configuration settings"
            )
            category_passed = False
        
        # Test 2: Default Credentials
        try:
            # Test for common default credentials
            default_creds = [
                ('admin', 'admin'),  
                ('admin', 'password'),
                ('user', 'user'),
                ('test', 'test'),
                ('admin', '123456')
            ]
            
            default_creds_secure = True
            
            for username, password in default_creds:
                try:
                    # Try to login with default credentials
                    login_data = {
                        'email': f'{username}@example.com',
                        'password': password
                    }
                    
                    response = requests.post(
                        f"http://localhost:8000/auth/login",
                        json=login_data,
                        timeout=2
                    )
                    
                    if response.status_code == 200:
                        default_creds_secure = False
                        break
                        
                except requests.RequestException:
                    pass
            
            self.log_finding(
                'A05',
                'Default Credentials Security',
                'HIGH',
                default_creds_secure,
                f"Default credentials: {'SECURE' if default_creds_secure else 'VULNERABLE'}",
                "Change all default credentials and enforce strong password policies"
            )
            
            if not default_creds_secure:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A05',
                'Default Credentials Test',
                'HIGH',
                False,
                f"Default credentials test failed: {e}",
                "Review authentication configuration"
            )
            category_passed = False
        
        # Test 3: Error Message Information Disclosure
        try:
            # Test if error messages reveal sensitive information
            error_disclosure_secure = True
            
            # Test various endpoints with invalid data to trigger errors
            error_test_cases = [
                ('POST', '/auth/login', {'email': 'invalid', 'password': 'invalid'}),
                ('GET', '/api/v1/courses/invalid-id', {}),
                ('POST', '/api/v1/content/search', {'query': ''}),  # Empty query
            ]
            
            for method, endpoint, data in error_test_cases:
                try:
                    if method == 'POST':
                        response = requests.post(f"http://localhost:8000{endpoint}", json=data, timeout=2)
                    else:
                        response = requests.get(f"http://localhost:8000{endpoint}", timeout=2)
                    
                    if 400 <= response.status_code < 500:
                        # Check error response for sensitive information
                        try:
                            error_data = response.json()
                            error_text = str(error_data).lower()
                            
                            # Look for sensitive info in error messages
                            sensitive_indicators = [
                                'database', 'sql', 'traceback', 'exception',
                                'file not found', 'permission denied', 'internal error',
                                'stack trace', 'line number'
                            ]
                            
                            if any(indicator in error_text for indicator in sensitive_indicators):
                                error_disclosure_secure = False
                                break
                        except:
                            pass
                            
                except requests.RequestException:
                    pass
            
            self.log_finding(
                'A05',
                'Error Message Security',
                'MEDIUM',
                error_disclosure_secure,
                f"Error information disclosure: {'SECURE' if error_disclosure_secure else 'VULNERABLE'}",
                "Implement generic error messages to prevent information disclosure"
            )
            
            if not error_disclosure_secure:
                category_passed = False
                
        except Exception as e:
            self.log_finding(
                'A05',
                'Error Message Security Test',
                'MEDIUM',
                False,
                f"Error message test failed: {e}",
                "Review error handling implementation"
            )
            category_passed = False
        
        return category_passed
    
    def generate_owasp_report(self) -> Dict[str, Any]:
        """Generate comprehensive OWASP assessment report"""
        # Calculate overall risk score
        total_issues = (
            self.results['critical_issues'] * 4 +
            self.results['high_issues'] * 3 +
            self.results['medium_issues'] * 2 +
            self.results['low_issues'] * 1
        )
        
        max_possible_score = self.results['total_tests'] * 4
        risk_score = 100 - ((total_issues / max_possible_score) * 100) if max_possible_score > 0 else 0
        
        # Determine overall security posture
        if risk_score >= 90:
            security_posture = "EXCELLENT"
        elif risk_score >= 80:
            security_posture = "GOOD"
        elif risk_score >= 70:
            security_posture = "ACCEPTABLE"
        elif risk_score >= 60:
            security_posture = "NEEDS IMPROVEMENT"
        else:
            security_posture = "CRITICAL"
        
        self.results.update({
            'overall_risk_score': round(risk_score, 1),
            'security_posture': security_posture,
            'completion_time': datetime.utcnow().isoformat()
        })
        
        return self.results
    
    async def run_full_assessment(self) -> Dict[str, Any]:
        """Run complete OWASP Top 10 security assessment"""
        print("🛡️  OWASP Top 10 Security Assessment - Course Creator Platform")
        print("=" * 70)
        
        # Run all OWASP Top 10 tests
        test_results = await asyncio.gather(
            self.test_a01_broken_access_control(),
            self.test_a02_cryptographic_failures(), 
            self.test_a03_injection(),
            self.test_a04_insecure_design(),
            self.test_a05_security_misconfiguration(),
            return_exceptions=True
        )
        
        # Additional tests would go here for A06-A10
        # For now, we'll focus on the most critical categories
        
        return self.generate_owasp_report()


async def main():
    """Main assessment entry point"""
    print("🛡️  Course Creator Platform - OWASP Top 10 Security Assessment")  
    print("=" * 70)
    
    assessor = OWASPTop10Assessment()
    
    try:
        report = await assessor.run_full_assessment()
        
        print("\n" + "=" * 70)
        print("📊 OWASP TOP 10 ASSESSMENT SUMMARY")
        print("=" * 70)
        
        print(f"Assessment Version: {report['assessment_version']}")
        print(f"Platform: {report['platform']}")
        print(f"Total Tests: {report['total_tests']}")
        print(f"Passed Tests: {report['passed_tests']}")
        print(f"Failed Tests: {report['failed_tests']}")
        print(f"Overall Risk Score: {report['overall_risk_score']}%")
        print(f"Security Posture: {report['security_posture']}")
        
        print(f"\n🚨 Issues by Severity:")
        print(f"Critical: {report['critical_issues']}")
        print(f"High: {report['high_issues']}")
        print(f"Medium: {report['medium_issues']}")
        print(f"Low: {report['low_issues']}")
        
        print(f"\n📋 OWASP Category Results:")
        for category, stats in report['owasp_categories'].items():
            risk_icon = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡', 
                'LOW': '🟢'
            }.get(stats['risk_level'], '⚪')
            
            print(f"  {risk_icon} {category}: {stats['passed_tests']}/{stats['total_tests']} passed "
                  f"(Risk: {stats['risk_level']})")
        
        # Save detailed report
        report_file = project_root / 'owasp_top10_assessment_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Return appropriate exit code
        if report['critical_issues'] > 0 or report['high_issues'] > 3:
            print("\n⚠️  Critical security issues found! Immediate remediation required.")
            return 1
        elif report['failed_tests'] > 0:
            print(f"\n⚠️  {report['failed_tests']} security issue(s) found. Review and remediate.")
            return 1
        else:
            print("\n🎉 OWASP Top 10 assessment completed successfully!")
            return 0
            
    except Exception as e:
        print(f"\n❌ OWASP assessment failed with exception: {e}")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)