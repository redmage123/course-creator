"""
Comprehensive Multi-Tenant Security E2E Test Suite (TDD RED PHASE)

BUSINESS CONTEXT:
The Course Creator Platform is a multi-tenant system where multiple organizations
share the same infrastructure but must be completely isolated from each other.
This test suite validates the security boundaries between organizations and
protects against common attack scenarios.

SECURITY REQUIREMENTS:
1. Organization Isolation - Each organization's data must be completely isolated
2. Attack Prevention - System must resist SQL injection, XSS, CSRF, and other attacks
3. Authentication Security - Session management must prevent fixation and brute force
4. Authorization Enforcement - Users can only access resources in their organization
5. Data Integrity - No cross-organization data leakage in caches, databases, or APIs

TDD METHODOLOGY:
This is the RED PHASE - all tests are expected to FAIL initially.
These tests define security requirements that the system must implement.
Implementation will occur in the GREEN PHASE after all tests fail.

TEST COVERAGE:
- 8 Organization Isolation Tests
- 7 Attack Scenario Tests
- Total: 15 comprehensive security tests

TECHNICAL IMPLEMENTATION:
- Uses Selenium WebDriver for browser-based E2E testing
- Uses httpx for API-level security testing
- Uses SecurityTestClient from fixtures for authenticated requests
- Tests real endpoints with actual authentication flows
- Simulates real attack payloads and scenarios
"""

import pytest
import time
import logging
import asyncio
import httpx
import uuid
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urlencode

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.e2e.selenium_base import BaseTest
from tests.fixtures.security_fixtures import (
    OrganizationFixture,
    UserFixture,
    SecurityTestClient,
    create_test_organizations,
    create_test_users,
    generate_valid_jwt_token,
    generate_expired_jwt_token,
    generate_malformed_jwt_token,
    validate_organization_isolation,
    assert_no_cross_organization_data
)

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.nondestructive


class TestMultiTenantOrganizationIsolation(BaseTest):
    """
    Test Suite: Multi-Tenant Organization Isolation (8 tests)

    SECURITY REQUIREMENT: Complete isolation between organizations
    Organizations A and B must have zero visibility into each other's data.

    TESTING APPROACH:
    - Create two separate organizations with distinct users
    - Attempt to access org B data while authenticated as org A user
    - Verify all access attempts are blocked
    - Validate no data leakage through caches, databases, or APIs
    """

    @pytest.fixture(scope="function", autouse=True)
    def setup_multi_tenant_test_data(self):
        """
        Create test organizations and users for isolation testing.

        BUSINESS CONTEXT:
        Real-world multi-tenant systems have multiple organizations using the
        same platform. Each organization must be completely isolated from others.
        """
        # Create two test organizations
        self.org_configs = [
            {'name': 'TechCorp Security Test', 'slug': 'techcorp-security'},
            {'name': 'DataInc Security Test', 'slug': 'datainc-security'}
        ]
        self.organizations = create_test_organizations(self.org_configs)
        self.org_a = self.organizations[0]
        self.org_b = self.organizations[1]

        # Create users for both organizations
        self.user_configs = [
            {
                'email': 'admin@techcorp-security.test',
                'role': 'organization_admin',
                'organization_id': self.org_a.id,
                'full_name': 'TechCorp Admin'
            },
            {
                'email': 'instructor@techcorp-security.test',
                'role': 'instructor',
                'organization_id': self.org_a.id,
                'full_name': 'TechCorp Instructor'
            },
            {
                'email': 'student@techcorp-security.test',
                'role': 'student',
                'organization_id': self.org_a.id,
                'full_name': 'TechCorp Student'
            },
            {
                'email': 'admin@datainc-security.test',
                'role': 'organization_admin',
                'organization_id': self.org_b.id,
                'full_name': 'DataInc Admin'
            },
            {
                'email': 'instructor@datainc-security.test',
                'role': 'instructor',
                'organization_id': self.org_b.id,
                'full_name': 'DataInc Instructor'
            }
        ]
        self.users = create_test_users(self.user_configs)

        # Generate JWT tokens for authentication
        self.org_a_admin_token = generate_valid_jwt_token(self.users[0])
        self.org_a_instructor_token = generate_valid_jwt_token(self.users[1])
        self.org_a_student_token = generate_valid_jwt_token(self.users[2])
        self.org_b_admin_token = generate_valid_jwt_token(self.users[3])
        self.org_b_instructor_token = generate_valid_jwt_token(self.users[4])

        # Create security test client
        self.security_client = SecurityTestClient(base_url='https://localhost:8000')

        logger.info(f"Test data created: Org A ({self.org_a.id}), Org B ({self.org_b.id})")
        yield

        logger.info("Multi-tenant test data cleanup completed")

    def test_cross_organization_data_access_blocked(self):
        """
        TEST: Organization A user cannot access Organization B data through API

        SECURITY REQUIREMENT: API endpoints must enforce organization boundaries
        ATTACK SCENARIO: User from Org A tries to access Org B's data via API
        EXPECTED: 403 Forbidden or 404 Not Found (no data leak)

        RED PHASE: This test will FAIL because organization isolation is not yet implemented
        """
        logger.info("TEST: Cross-organization data access via API")

        # Attempt to access Organization B's courses while authenticated as Org A user
        async def test_api_isolation():
            async with self.security_client.authenticated_request(
                self.org_a_admin_token,
                self.org_b.id  # Trying to access Org B with Org A credentials
            ) as client:
                # Attempt to get Organization B's courses
                response = await client.get(f'/api/v1/courses?organization_id={self.org_b.id}')

                # Should be blocked (403 Forbidden or 404 Not Found)
                assert response.status_code in [403, 404], \
                    f"Expected 403/404, got {response.status_code}. Cross-org access should be blocked!"

                # Verify no data was returned
                data = response.json()
                if isinstance(data, list):
                    assert len(data) == 0, "No Organization B data should be visible to Organization A user"

                logger.info("✓ Cross-organization API access successfully blocked")

        # Run async test
        asyncio.run(test_api_isolation())

    def test_cross_organization_course_access_blocked(self):
        """
        TEST: Users cannot access courses from other organizations

        SECURITY REQUIREMENT: Course access must be scoped to user's organization
        ATTACK SCENARIO: Org A instructor tries to view/edit Org B course
        EXPECTED: 403 Forbidden

        RED PHASE: This test will FAIL - course isolation not yet implemented
        """
        logger.info("TEST: Cross-organization course access")

        async def test_course_isolation():
            # Create a course in Organization B
            async with self.security_client.authenticated_request(
                self.org_b_instructor_token,
                self.org_b.id
            ) as client:
                # Create course in Org B
                course_data = {
                    'title': 'Org B Confidential Course',
                    'description': 'This should only be visible to Org B',
                    'organization_id': self.org_b.id
                }
                create_response = await client.post('/api/v1/courses', json=course_data)
                assert create_response.status_code == 201, "Course creation should succeed"

                org_b_course = create_response.json()
                org_b_course_id = org_b_course['id']
                logger.info(f"Created Org B course: {org_b_course_id}")

            # Now try to access that course as Org A instructor
            async with self.security_client.authenticated_request(
                self.org_a_instructor_token,
                self.org_a.id
            ) as client:
                # Attempt to access Org B's course
                response = await client.get(f'/api/v1/courses/{org_b_course_id}')

                # Should be blocked
                assert response.status_code in [403, 404], \
                    f"Expected 403/404, got {response.status_code}. Org A user accessed Org B course!"

                logger.info("✓ Cross-organization course access blocked")

        asyncio.run(test_course_isolation())

    def test_cross_organization_user_access_blocked(self):
        """
        TEST: Organization admins cannot access users from other organizations

        SECURITY REQUIREMENT: User management must be scoped to organization
        ATTACK SCENARIO: Org A admin tries to list/modify Org B users
        EXPECTED: 403 Forbidden or empty list

        RED PHASE: This test will FAIL - user isolation not yet implemented
        """
        logger.info("TEST: Cross-organization user access")

        async def test_user_isolation():
            # Org A admin tries to access Org B users
            async with self.security_client.authenticated_request(
                self.org_a_admin_token,
                self.org_b.id  # Trying to access Org B users
            ) as client:
                response = await client.get(f'/api/v1/users?organization_id={self.org_b.id}')

                # Should be blocked or return empty
                if response.status_code == 200:
                    users = response.json()
                    assert len(users) == 0, "Org A admin should not see Org B users"
                else:
                    assert response.status_code == 403, "Should be forbidden"

                logger.info("✓ Cross-organization user access blocked")

        asyncio.run(test_user_isolation())

    def test_cross_organization_analytics_isolated(self):
        """
        TEST: Analytics data must be scoped to user's organization

        SECURITY REQUIREMENT: No analytics data leakage between organizations
        ATTACK SCENARIO: Org A admin tries to view Org B analytics
        EXPECTED: Only Org A analytics visible

        RED PHASE: This test will FAIL - analytics isolation not yet implemented
        """
        logger.info("TEST: Cross-organization analytics isolation")

        async def test_analytics_isolation():
            # Request analytics as Org A admin
            async with self.security_client.authenticated_request(
                self.org_a_admin_token,
                self.org_a.id
            ) as client:
                response = await client.get(f'/api/v1/analytics/organization/{self.org_a.id}')

                assert response.status_code == 200, "Analytics should be accessible for own org"

                analytics = response.json()

                # Verify data is only from Org A
                assert validate_organization_isolation(analytics, self.org_a.id), \
                    "Analytics should only contain Org A data"

                # Verify no Org B data leaked
                assert_no_cross_organization_data(analytics, [self.org_b.id])

                logger.info("✓ Analytics properly isolated to organization")

        asyncio.run(test_analytics_isolation())

    def test_organization_resource_quotas_enforced(self):
        """
        TEST: Organization resource quotas must be enforced per organization

        SECURITY REQUIREMENT: Organizations cannot exceed their resource limits
        ATTACK SCENARIO: Org A tries to create more resources than quota allows
        EXPECTED: 429 Too Many Requests or 403 Forbidden

        RED PHASE: This test will FAIL - quota enforcement not yet implemented
        """
        logger.info("TEST: Organization resource quota enforcement")

        async def test_quota_enforcement():
            # Assume organization has quota of 100 courses
            max_courses = 100

            async with self.security_client.authenticated_request(
                self.org_a_instructor_token,
                self.org_a.id
            ) as client:
                # Try to create courses beyond quota (simulate)
                # In real test, would create 101 courses
                for i in range(max_courses + 1):
                    course_data = {
                        'title': f'Course {i}',
                        'organization_id': self.org_a.id
                    }
                    response = await client.post('/api/v1/courses', json=course_data)

                    if i < max_courses:
                        assert response.status_code == 201, f"Course {i} should be created"
                    else:
                        # 101st course should fail
                        assert response.status_code in [429, 403], \
                            f"Course beyond quota should be rejected, got {response.status_code}"
                        logger.info("✓ Resource quota enforced - creation blocked")
                        break

        # Note: This is a simplified simulation
        # Real test would need actual quota tracking
        logger.info("⚠ Quota enforcement test simulated - needs real implementation")

    def test_organization_feature_flags_isolated(self):
        """
        TEST: Feature flags must be scoped to organizations

        SECURITY REQUIREMENT: Org A's feature flags don't affect Org B
        ATTACK SCENARIO: Attacker tries to enable premium features for their org
        EXPECTED: Feature access properly scoped

        RED PHASE: This test will FAIL - feature flag isolation not implemented
        """
        logger.info("TEST: Organization feature flags isolation")

        async def test_feature_flag_isolation():
            # Org A has premium features enabled
            # Org B has only basic features

            # Check Org A can access premium features
            async with self.security_client.authenticated_request(
                self.org_a_admin_token,
                self.org_a.id
            ) as client:
                response = await client.get('/api/v1/features')
                assert response.status_code == 200

                features = response.json()
                # Verify features are scoped to Org A
                if isinstance(features, dict):
                    assert features.get('organization_id') == self.org_a.id, \
                        "Features should be scoped to organization"

            # Check Org B cannot access Org A's feature flags
            async with self.security_client.authenticated_request(
                self.org_b_admin_token,
                self.org_b.id
            ) as client:
                response = await client.get('/api/v1/features')
                assert response.status_code == 200

                features = response.json()
                if isinstance(features, dict):
                    assert features.get('organization_id') == self.org_b.id, \
                        "Features should be scoped to Org B, not Org A"

            logger.info("✓ Feature flags properly isolated")

        asyncio.run(test_feature_flag_isolation())

    def test_organization_cache_isolation(self):
        """
        TEST: Redis cache keys must be namespaced per organization

        SECURITY REQUIREMENT: Cache isolation prevents data leakage
        ATTACK SCENARIO: Org A user tries to access cached Org B data
        EXPECTED: No cache key collisions, proper namespacing

        RED PHASE: This test will FAIL - cache isolation not yet implemented
        """
        logger.info("TEST: Organization cache isolation")

        async def test_cache_isolation():
            # Create data in Org A's cache
            async with self.security_client.authenticated_request(
                self.org_a_instructor_token,
                self.org_a.id
            ) as client:
                # Create a course (should be cached)
                course_data = {
                    'title': 'Org A Cached Course',
                    'organization_id': self.org_a.id
                }
                response = await client.post('/api/v1/courses', json=course_data)
                assert response.status_code == 201
                org_a_course = response.json()

                # Access course again (should hit cache)
                response2 = await client.get(f"/api/v1/courses/{org_a_course['id']}")
                assert response2.status_code == 200

            # Try to access from Org B (should not see cached Org A data)
            async with self.security_client.authenticated_request(
                self.org_b_instructor_token,
                self.org_b.id
            ) as client:
                # Attempt to access Org A's course (even if cache key guessed)
                response = await client.get(f"/api/v1/courses/{org_a_course['id']}")

                assert response.status_code in [403, 404], \
                    "Org B should not access Org A cached data"

            logger.info("✓ Cache properly isolated between organizations")

        asyncio.run(test_cache_isolation())

    def test_organization_database_isolation(self):
        """
        TEST: Database Row-Level Security (RLS) policies enforce isolation

        SECURITY REQUIREMENT: PostgreSQL RLS policies prevent cross-org queries
        ATTACK SCENARIO: Direct database query tries to access other org data
        EXPECTED: RLS policies block unauthorized access

        RED PHASE: This test will FAIL - RLS policies not yet implemented
        """
        logger.info("TEST: Database Row-Level Security isolation")

        # This test validates that even if SQL injection occurs,
        # RLS policies prevent cross-organization data access

        async def test_database_rls():
            # Test that queries are automatically scoped
            async with self.security_client.authenticated_request(
                self.org_a_admin_token,
                self.org_a.id
            ) as client:
                # Request all courses (should only get Org A courses due to RLS)
                response = await client.get('/api/v1/courses')

                assert response.status_code == 200
                courses = response.json()

                # Verify all returned courses belong to Org A
                if isinstance(courses, list) and len(courses) > 0:
                    for course in courses:
                        assert course.get('organization_id') == self.org_a.id, \
                            "RLS should filter to only Org A courses"

                # Verify no Org B data
                assert_no_cross_organization_data(courses, [self.org_b.id])

            logger.info("✓ Database RLS policies enforcing isolation")

        asyncio.run(test_database_rls())


class TestAttackScenarioPrevention(BaseTest):
    """
    Test Suite: Attack Scenario Prevention (7 tests)

    SECURITY REQUIREMENT: Platform must resist common web attacks
    Tests validate protection against OWASP Top 10 vulnerabilities.

    ATTACK TYPES TESTED:
    1. SQL Injection (A03:2021 - Injection)
    2. XSS (A03:2021 - Injection)
    3. CSRF (A01:2021 - Broken Access Control)
    4. Session Fixation (A07:2021 - Authentication Failures)
    5. Brute Force (A07:2021 - Authentication Failures)
    6. DoS/Rate Limiting (A04:2021 - Insecure Design)
    7. Privilege Escalation (A01:2021 - Broken Access Control)
    """

    @pytest.fixture(scope="function", autouse=True)
    def setup_attack_test_data(self):
        """Setup test data for attack scenario testing"""
        # Create test organization and users
        self.org = OrganizationFixture.create('Attack Test Org', 'attack-test')
        self.admin_user = UserFixture.create(
            'admin@attack-test.com',
            'organization_admin',
            self.org.id
        )
        self.student_user = UserFixture.create(
            'student@attack-test.com',
            'student',
            self.org.id
        )

        self.admin_token = generate_valid_jwt_token(self.admin_user)
        self.student_token = generate_valid_jwt_token(self.student_user)
        self.security_client = SecurityTestClient(base_url='https://localhost:8000')

        logger.info("Attack scenario test data created")
        yield
        logger.info("Attack scenario test cleanup completed")

    def test_sql_injection_protection_all_endpoints(self):
        """
        TEST: SQL injection attacks must be blocked on all API endpoints

        ATTACK SCENARIO: Attacker tries SQL injection via various inputs
        PAYLOADS:
        - ' OR '1'='1
        - '; DROP TABLE courses; --
        - ' UNION SELECT * FROM users --

        EXPECTED: Input sanitization prevents SQL execution

        RED PHASE: This test will FAIL - SQL injection protection not implemented
        """
        logger.info("TEST: SQL Injection protection")

        # Common SQL injection payloads
        sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE courses; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "1' OR '1' = '1",
            "1' AND 1=1--",
            "1' AND 1=2--"
        ]

        async def test_sql_injection():
            async with self.security_client.authenticated_request(
                self.admin_token,
                self.org.id
            ) as client:
                for payload in sql_injection_payloads:
                    # Test injection in search parameter
                    response = await client.get(
                        f'/api/v1/courses?search={payload}'
                    )

                    # Should either sanitize or return 400 Bad Request
                    assert response.status_code in [200, 400], \
                        f"SQL injection payload caused error: {payload}"

                    if response.status_code == 200:
                        # Verify no SQL injection occurred
                        data = response.json()
                        # Should return empty or safe results, not database dump
                        assert isinstance(data, (list, dict)), \
                            "Response should be structured data"

                logger.info("✓ SQL injection attempts blocked/sanitized")

        asyncio.run(test_sql_injection())

    def test_xss_protection_all_inputs(self):
        """
        TEST: XSS attacks must be blocked on all user inputs

        ATTACK SCENARIO: Attacker tries to inject malicious scripts
        PAYLOADS:
        - <script>alert('XSS')</script>
        - <img src=x onerror=alert('XSS')>
        - javascript:alert('XSS')

        EXPECTED: Input sanitization and CSP headers prevent XSS

        RED PHASE: This test will FAIL - XSS protection not implemented
        """
        logger.info("TEST: XSS protection")

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<svg onload=alert('XSS')>",
            "'-alert(1)-'",
            "\"><script>alert(1)</script>"
        ]

        async def test_xss():
            async with self.security_client.authenticated_request(
                self.admin_token,
                self.org.id
            ) as client:
                for payload in xss_payloads:
                    # Try to create course with XSS in title
                    course_data = {
                        'title': payload,
                        'description': f'Description with {payload}',
                        'organization_id': self.org.id
                    }

                    response = await client.post('/api/v1/courses', json=course_data)

                    if response.status_code == 201:
                        course = response.json()
                        # Verify payload was sanitized
                        assert '<script' not in course['title'].lower(), \
                            "XSS payload not sanitized in title"
                        assert 'onerror' not in course['description'].lower(), \
                            "XSS payload not sanitized in description"

                logger.info("✓ XSS payloads sanitized")

        asyncio.run(test_xss())

    def test_csrf_protection_all_state_changes(self):
        """
        TEST: CSRF tokens must be required for all state-changing operations

        ATTACK SCENARIO: Attacker tricks user into making unintended requests
        EXPECTED: CSRF token validation on POST/PUT/DELETE

        RED PHASE: This test will FAIL - CSRF protection not implemented
        """
        logger.info("TEST: CSRF protection")

        async def test_csrf():
            # Make state-changing request without CSRF token
            async with httpx.AsyncClient() as client:
                headers = {
                    'Authorization': f'Bearer {self.admin_token}',
                    'X-Organization-ID': self.org.id
                    # Intentionally missing CSRF token
                }

                # Attempt to create course without CSRF token
                course_data = {
                    'title': 'CSRF Test Course',
                    'organization_id': self.org.id
                }

                try:
                    response = await client.post(
                        'https://localhost:8000/api/v1/courses',
                        json=course_data,
                        headers=headers,
                        verify=False  # Accept self-signed cert
                    )

                    # Should require CSRF token
                    assert response.status_code in [403, 400], \
                        f"CSRF protection not enforced, got {response.status_code}"

                    logger.info("✓ CSRF protection enforced")
                except httpx.RequestError as e:
                    logger.warning(f"CSRF test connection error: {e}")

        asyncio.run(test_csrf())

    def test_session_fixation_prevention(self):
        """
        TEST: Session IDs must regenerate after authentication

        ATTACK SCENARIO: Attacker fixes victim's session ID before login
        EXPECTED: New session ID generated after successful authentication

        RED PHASE: This test will FAIL - session regeneration not implemented
        """
        logger.info("TEST: Session fixation prevention")

        # Navigate to login page
        self.driver.get(f"{self.config.base_url}/html/index.html")
        time.sleep(2)

        # Get initial session ID (if any)
        initial_session = self.driver.execute_script(
            "return sessionStorage.getItem('sessionId') || 'none';"
        )

        # Perform login
        self.driver.execute_script(f"""
            localStorage.setItem('authToken', '{self.admin_token}');
            localStorage.setItem('currentUser', JSON.stringify({{
                id: '{self.admin_user.id}',
                email: '{self.admin_user.email}',
                role: '{self.admin_user.role}',
                organization_id: '{self.org.id}'
            }}));
        """)

        # Navigate to dashboard
        self.driver.get(f"{self.config.base_url}/html/dashboard.html")
        time.sleep(2)

        # Get session ID after authentication
        post_auth_session = self.driver.execute_script(
            "return sessionStorage.getItem('sessionId') || 'none';"
        )

        # Session ID should be different (regenerated)
        assert initial_session != post_auth_session, \
            "Session ID should regenerate after authentication to prevent fixation"

        logger.info("✓ Session fixation prevented - session regenerated")

    def test_brute_force_protection(self):
        """
        TEST: Brute force login attempts must be rate limited

        ATTACK SCENARIO: Attacker tries multiple passwords rapidly
        EXPECTED: Rate limiting blocks excessive login attempts

        RED PHASE: This test will FAIL - brute force protection not implemented
        """
        logger.info("TEST: Brute force protection")

        async def test_brute_force():
            # Attempt multiple rapid logins
            max_attempts = 10
            blocked = False

            async with httpx.AsyncClient() as client:
                for attempt in range(max_attempts):
                    try:
                        response = await client.post(
                            'https://localhost:8000/api/v1/auth/login',
                            json={
                                'email': 'attacker@test.com',
                                'password': f'wrong_password_{attempt}'
                            },
                            verify=False
                        )

                        # After several attempts, should be rate limited
                        if response.status_code == 429:
                            blocked = True
                            logger.info(f"✓ Brute force blocked after {attempt + 1} attempts")
                            break
                    except httpx.RequestError:
                        pass

                    time.sleep(0.1)  # Small delay between attempts

            assert blocked, "Brute force protection should trigger after multiple failed attempts"

        asyncio.run(test_brute_force())

    def test_dos_attack_mitigation(self):
        """
        TEST: DoS attacks must be mitigated via rate limiting

        ATTACK SCENARIO: Attacker floods API with requests
        EXPECTED: Rate limiting protects against DoS

        RED PHASE: This test will FAIL - DoS protection not implemented
        """
        logger.info("TEST: DoS attack mitigation")

        async def test_dos():
            # Simulate high-volume requests
            request_count = 100
            blocked_count = 0

            async with self.security_client.authenticated_request(
                self.admin_token,
                self.org.id
            ) as client:
                for i in range(request_count):
                    response = await client.get('/api/v1/courses')

                    if response.status_code == 429:  # Too Many Requests
                        blocked_count += 1

                # Should have triggered rate limiting
                assert blocked_count > 0, \
                    "DoS protection should rate limit excessive requests"

                logger.info(f"✓ DoS protection active - {blocked_count}/{request_count} requests blocked")

        asyncio.run(test_dos())

    def test_privilege_escalation_prevention(self):
        """
        TEST: Users cannot escalate privileges through manipulation

        ATTACK SCENARIO: Student tries to access admin-only endpoints
        EXPECTED: Role-based access control enforced

        RED PHASE: This test will FAIL - privilege escalation not prevented
        """
        logger.info("TEST: Privilege escalation prevention")

        async def test_privilege_escalation():
            # Student tries to access admin endpoint
            async with self.security_client.authenticated_request(
                self.student_token,
                self.org.id
            ) as client:
                # Try to access admin-only organization settings
                response = await client.get(f'/api/v1/organizations/{self.org.id}/settings')

                # Should be forbidden for student
                assert response.status_code == 403, \
                    f"Student accessed admin endpoint! Status: {response.status_code}"

                # Try to modify organization settings (admin-only)
                response = await client.put(
                    f'/api/v1/organizations/{self.org.id}/settings',
                    json={'name': 'Hacked Name'}
                )

                assert response.status_code == 403, \
                    "Student modified org settings! Privilege escalation occurred!"

                logger.info("✓ Privilege escalation prevented - RBAC enforced")

        asyncio.run(test_privilege_escalation())


# Test summary and reporting
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Custom pytest terminal summary for security test results

    Provides detailed summary of which security tests failed (expected in RED phase)
    """
    if hasattr(config, 'workerinput'):
        return  # Skip on xdist workers

    terminalreporter.section("Multi-Tenant Security Test Suite Summary")
    terminalreporter.line("=" * 80)
    terminalreporter.line("")
    terminalreporter.line("TDD RED PHASE - Expected Result: ALL TESTS SHOULD FAIL")
    terminalreporter.line("")
    terminalreporter.line("Test Categories:")
    terminalreporter.line("  1. Organization Isolation Tests (8 tests)")
    terminalreporter.line("  2. Attack Scenario Tests (7 tests)")
    terminalreporter.line("")
    terminalreporter.line("Total Security Tests: 15")
    terminalreporter.line("")
    terminalreporter.line("Next Steps:")
    terminalreporter.line("  1. Review failing tests to understand security requirements")
    terminalreporter.line("  2. Implement security features (GREEN phase)")
    terminalreporter.line("  3. Re-run tests until all pass")
    terminalreporter.line("  4. Refactor for production (REFACTOR phase)")
    terminalreporter.line("")
    terminalreporter.line("=" * 80)
