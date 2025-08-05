"""
End-to-End Security Tests for Multi-Tenant Organization Isolation

TESTING STRATEGY:
Comprehensive end-to-end testing of the complete security system to ensure
proper multi-tenant isolation across all application layers and prevent
any possible cross-organization data access or privilege escalation.

TEST CATEGORIES:
1. Complete User Workflows - Full authentication to data access flows
2. Cross-Organization Boundary Testing - Verify isolation between tenants
3. API Security - REST endpoint security with organization context
4. Cache Security Integration - Redis cache isolation verification
5. Database Security - Row-level security policy validation
6. Real-World Attack Scenarios - Practical security breach attempts

SECURITY COVERAGE:
- Complete request lifecycle from authentication to database
- Multi-service integration with organization context propagation
- Cache and database isolation across organization boundaries
- API endpoint security with proper authorization
- Real-world attack pattern prevention
- Performance under security constraints
"""

import pytest
import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

import httpx
import jwt
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock

# Test utilities
from tests.fixtures.security_fixtures import (
    OrganizationFixture, UserFixture, SecurityTestClient,
    create_test_organizations, create_test_users, 
    generate_valid_jwt_token, generate_expired_jwt_token
)


class TestCompleteSecurityWorkflows:
    """End-to-end tests for complete security workflows"""
    
    @pytest.fixture
    def test_organizations(self):
        """Create test organizations for isolation testing"""
        return create_test_organizations([
            {'name': 'TechCorp Academy', 'slug': 'techcorp'},
            {'name': 'EduInnovate', 'slug': 'eduinnovate'},
            {'name': 'SkillBuilder Inc', 'slug': 'skillbuilder'}
        ])
    
    @pytest.fixture
    def test_users(self, test_organizations):
        """Create test users across different organizations"""
        org_techcorp, org_eduinnovate, org_skillbuilder = test_organizations
        
        return create_test_users([
            # TechCorp users
            {'email': 'admin@techcorp.com', 'role': 'admin', 'organization_id': org_techcorp.id},
            {'email': 'instructor1@techcorp.com', 'role': 'instructor', 'organization_id': org_techcorp.id},
            {'email': 'student1@techcorp.com', 'role': 'student', 'organization_id': org_techcorp.id},
            
            # EduInnovate users
            {'email': 'admin@eduinnovate.com', 'role': 'admin', 'organization_id': org_eduinnovate.id},
            {'email': 'instructor1@eduinnovate.com', 'role': 'instructor', 'organization_id': org_eduinnovate.id},
            {'email': 'student1@eduinnovate.com', 'role': 'student', 'organization_id': org_eduinnovate.id},
            
            # SkillBuilder users
            {'email': 'admin@skillbuilder.com', 'role': 'admin', 'organization_id': org_skillbuilder.id},
            {'email': 'instructor1@skillbuilder.com', 'role': 'instructor', 'organization_id': org_skillbuilder.id},
        ])
    
    @pytest.fixture
    def security_client(self):
        """Create security-aware test client"""
        return SecurityTestClient()

    async def test_complete_instructor_workflow_with_organization_isolation(
        self, security_client, test_organizations, test_users
    ):
        """
        Test complete instructor workflow with strict organization isolation
        
        WORKFLOW:
        1. Instructor logs in and gets JWT token
        2. Creates course within their organization
        3. Attempts to access other organization's courses (should fail)
        4. Manages students within organization boundary
        5. Views analytics scoped to organization
        """
        
        org_techcorp, org_eduinnovate, org_skillbuilder = test_organizations
        instructor_techcorp = next(u for u in test_users if u.email == 'instructor1@techcorp.com')
        instructor_eduinnovate = next(u for u in test_users if u.email == 'instructor1@eduinnovate.com')
        
        # Step 1: Instructor authentication
        jwt_token = generate_valid_jwt_token(instructor_techcorp)
        
        # Step 2: Create course within organization
        course_data = {
            'title': 'Advanced Python Programming',
            'description': 'Comprehensive Python course for TechCorp',
            'category': 'programming',
            'difficulty_level': 'advanced',
            'estimated_duration': 12,
            'duration_unit': 'weeks'
        }
        
        async with security_client.authenticated_request(
            jwt_token, org_techcorp.id
        ) as client:
            # Create course
            response = await client.post('/api/v1/courses', json=course_data)
            assert response.status_code == 201
            
            created_course = response.json()
            course_id = created_course['id']
            
            # Verify course is created within organization
            assert created_course['instructor_id'] == instructor_techcorp.id
            
            # Step 3: Verify instructor can access their own courses
            response = await client.get('/api/v1/courses')
            assert response.status_code == 200
            
            courses = response.json()
            assert len(courses) == 1
            assert courses[0]['id'] == course_id
        
        # Step 4: Attempt cross-organization access (should fail)
        async with security_client.authenticated_request(
            jwt_token, org_eduinnovate.id  # Wrong organization
        ) as client:
            # Should not be able to access courses from different organization
            response = await client.get('/api/v1/courses')
            assert response.status_code == 403
            assert 'Access denied' in response.json()['detail']
            
            # Should not be able to access specific course from different organization
            response = await client.get(f'/api/v1/courses/{course_id}')
            assert response.status_code == 403

    async def test_student_enrollment_boundary_enforcement(
        self, security_client, test_organizations, test_users
    ):
        """
        Test student enrollment respects organization boundaries
        
        SECURITY REQUIREMENT:
        Students should only be able to enroll in courses within their organization
        and should not see or access courses from other organizations.
        """
        
        org_techcorp, org_eduinnovate, _ = test_organizations
        student_techcorp = next(u for u in test_users if u.email == 'student1@techcorp.com')
        student_eduinnovate = next(u for u in test_users if u.email == 'student1@eduinnovate.com')
        instructor_eduinnovate = next(u for u in test_users if u.email == 'instructor1@eduinnovate.com')
        
        # Create course in EduInnovate organization
        instructor_token = generate_valid_jwt_token(instructor_eduinnovate)
        
        course_data = {
            'title': 'Data Science Fundamentals',
            'description': 'Data science course for EduInnovate students',
            'category': 'data-science',
            'difficulty_level': 'beginner'
        }
        
        async with security_client.authenticated_request(
            instructor_token, org_eduinnovate.id
        ) as client:
            response = await client.post('/api/v1/courses', json=course_data)
            assert response.status_code == 201
            eduinnovate_course_id = response.json()['id']
        
        # TechCorp student attempts to access EduInnovate course
        student_token = generate_valid_jwt_token(student_techcorp)
        
        async with security_client.authenticated_request(
            student_token, org_techcorp.id
        ) as client:
            # Should not see EduInnovate courses in published course list
            response = await client.get('/api/v1/courses/published')
            assert response.status_code == 200
            
            published_courses = response.json()
            eduinnovate_course_ids = [c['id'] for c in published_courses if c['id'] == eduinnovate_course_id]
            assert len(eduinnovate_course_ids) == 0, "Student should not see courses from other organizations"
            
            # Should not be able to enroll in EduInnovate course
            enrollment_data = {
                'student_email': student_techcorp.email,
                'course_id': eduinnovate_course_id
            }
            
            response = await client.post('/api/v1/enrollments', json=enrollment_data)
            assert response.status_code == 403 or response.status_code == 404

    async def test_cache_isolation_across_organizations(
        self, security_client, test_organizations, test_users
    ):
        """
        Test cache isolation prevents cross-organization data access
        
        CACHE SECURITY:
        Verify that cached data (courses, user sessions, analytics) is properly
        isolated between organizations and cannot be accessed across boundaries.
        """
        
        org_techcorp, org_eduinnovate, _ = test_organizations
        instructor_techcorp = next(u for u in test_users if u.email == 'instructor1@techcorp.com')
        instructor_eduinnovate = next(u for u in test_users if u.email == 'instructor1@eduinnovate.com')
        
        # Create courses in both organizations
        techcorp_token = generate_valid_jwt_token(instructor_techcorp)
        eduinnovate_token = generate_valid_jwt_token(instructor_eduinnovate)
        
        course_data_techcorp = {
            'title': 'TechCorp Confidential Training',
            'description': 'Internal confidential training material',
            'category': 'internal'
        }
        
        course_data_eduinnovate = {
            'title': 'EduInnovate Private Course',
            'description': 'Private course with sensitive content',
            'category': 'private'
        }
        
        # Create and cache courses
        async with security_client.authenticated_request(
            techcorp_token, org_techcorp.id
        ) as client:
            response = await client.post('/api/v1/courses', json=course_data_techcorp)
            assert response.status_code == 201
            techcorp_course_id = response.json()['id']
            
            # Access course to trigger caching
            response = await client.get(f'/api/v1/courses/{techcorp_course_id}')
            assert response.status_code == 200
        
        async with security_client.authenticated_request(
            eduinnovate_token, org_eduinnovate.id
        ) as client:
            response = await client.post('/api/v1/courses', json=course_data_eduinnovate)
            assert response.status_code == 201
            eduinnovate_course_id = response.json()['id']
            
            # Access course to trigger caching
            response = await client.get(f'/api/v1/courses/{eduinnovate_course_id}')
            assert response.status_code == 200
        
        # Attempt cross-organization cache access
        async with security_client.authenticated_request(
            techcorp_token, org_techcorp.id
        ) as client:
            # Should not be able to access EduInnovate course (even if cached)
            response = await client.get(f'/api/v1/courses/{eduinnovate_course_id}')
            assert response.status_code == 403 or response.status_code == 404
        
        async with security_client.authenticated_request(
            eduinnovate_token, org_eduinnovate.id
        ) as client:
            # Should not be able to access TechCorp course (even if cached)
            response = await client.get(f'/api/v1/courses/{techcorp_course_id}')
            assert response.status_code == 403 or response.status_code == 404

    async def test_analytics_data_isolation(
        self, security_client, test_organizations, test_users
    ):
        """
        Test analytics data is properly isolated between organizations
        
        ANALYTICS SECURITY:
        Organization admins should only see analytics data for their organization
        and should not access or infer data from other organizations.
        """
        
        org_techcorp, org_eduinnovate, _ = test_organizations
        admin_techcorp = next(u for u in test_users if u.email == 'admin@techcorp.com')
        admin_eduinnovate = next(u for u in test_users if u.email == 'admin@eduinnovate.com')
        
        techcorp_token = generate_valid_jwt_token(admin_techcorp)
        eduinnovate_token = generate_valid_jwt_token(admin_eduinnovate)
        
        # Access analytics for each organization
        async with security_client.authenticated_request(
            techcorp_token, org_techcorp.id
        ) as client:
            response = await client.get('/api/v1/analytics/dashboard')
            assert response.status_code == 200
            
            techcorp_analytics = response.json()
            assert 'organization_id' in techcorp_analytics
            assert techcorp_analytics['organization_id'] == org_techcorp.id
        
        async with security_client.authenticated_request(
            eduinnovate_token, org_eduinnovate.id
        ) as client:
            response = await client.get('/api/v1/analytics/dashboard')
            assert response.status_code == 200
            
            eduinnovate_analytics = response.json()
            assert 'organization_id' in eduinnovate_analytics
            assert eduinnovate_analytics['organization_id'] == org_eduinnovate.id
        
        # Verify data isolation
        assert techcorp_analytics['organization_id'] != eduinnovate_analytics['organization_id']
        
        # Attempt cross-organization analytics access
        async with security_client.authenticated_request(
            techcorp_token, org_eduinnovate.id  # Wrong organization
        ) as client:
            response = await client.get('/api/v1/analytics/dashboard')
            assert response.status_code == 403

    async def test_concurrent_multi_organization_access(
        self, security_client, test_organizations, test_users
    ):
        """
        Test system behavior under concurrent multi-organization access
        
        PERFORMANCE SECURITY:
        Ensure security controls don't degrade under load and that
        concurrent access from multiple organizations remains isolated.
        """
        
        org_techcorp, org_eduinnovate, org_skillbuilder = test_organizations
        
        # Create tokens for users from different organizations
        users_by_org = {
            org_techcorp.id: [u for u in test_users if u.organization_id == org_techcorp.id],
            org_eduinnovate.id: [u for u in test_users if u.organization_id == org_eduinnovate.id],
            org_skillbuilder.id: [u for u in test_users if u.organization_id == org_skillbuilder.id],
        }
        
        async def organization_workflow(org_id: str, users: List[UserFixture]):
            """Simulate typical organization workflow"""
            results = []
            
            for user in users:
                token = generate_valid_jwt_token(user)
                
                async with security_client.authenticated_request(token, org_id) as client:
                    # Each user tries to access their organization's resources
                    response = await client.get('/api/v1/courses')
                    results.append({
                        'user_id': user.id,
                        'organization_id': org_id,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    })
                    
                    # Try to access other organization's resources (should fail)
                    other_orgs = [oid for oid in users_by_org.keys() if oid != org_id]
                    for other_org_id in other_orgs:
                        async with security_client.authenticated_request(token, other_org_id) as other_client:
                            response = await other_client.get('/api/v1/courses')
                            results.append({
                                'user_id': user.id,
                                'attempted_organization_id': other_org_id,
                                'status_code': response.status_code,
                                'blocked': response.status_code == 403
                            })
            
            return results
        
        # Run concurrent workflows for all organizations
        tasks = [
            organization_workflow(org_id, users)
            for org_id, users in users_by_org.items()
        ]
        
        all_results = await asyncio.gather(*tasks)
        
        # Verify all legitimate access succeeded
        legitimate_access = [
            result for org_results in all_results 
            for result in org_results 
            if 'success' in result
        ]
        assert all(result['success'] for result in legitimate_access)
        
        # Verify all cross-organization access was blocked
        blocked_access = [
            result for org_results in all_results 
            for result in org_results 
            if 'blocked' in result
        ]
        assert all(result['blocked'] for result in blocked_access)


class TestRealWorldAttackScenarios:
    """Tests simulating real-world attack scenarios"""
    
    @pytest.fixture
    def attacker_setup(self, test_organizations, test_users):
        """Set up attacker and target scenarios"""
        org_target = test_organizations[0]  # TechCorp
        org_attacker = test_organizations[1]  # EduInnovate
        
        target_admin = next(u for u in test_users if u.email == 'admin@techcorp.com')
        attacker_user = next(u for u in test_users if u.email == 'instructor1@eduinnovate.com')
        
        return {
            'target_org': org_target,
            'attacker_org': org_attacker,
            'target_admin': target_admin,
            'attacker_user': attacker_user
        }

    async def test_jwt_token_manipulation_attack(self, security_client, attacker_setup):
        """
        Test prevention of JWT token manipulation attacks
        
        ATTACK SCENARIO:
        Attacker modifies JWT token to change organization_id or user_id
        to gain unauthorized access to other organizations' data.
        """
        
        attacker_user = attacker_setup['attacker_user']
        target_org = attacker_setup['target_org']
        
        # Generate legitimate token for attacker
        legitimate_token = generate_valid_jwt_token(attacker_user)
        
        # Decode token to manipulate it
        secret_key = 'test-secret-key-for-testing'
        payload = jwt.decode(legitimate_token, secret_key, algorithms=['HS256'])
        
        # Manipulation attempts
        manipulation_attempts = [
            # Change user ID to target admin
            {**payload, 'sub': attacker_setup['target_admin'].id},
            # Add fake organization claim
            {**payload, 'organization_id': target_org.id},
            # Change role to admin
            {**payload, 'role': 'super_admin'},
            # Extend expiration
            {**payload, 'exp': datetime.utcnow() + timedelta(days=365)},
        ]
        
        for manipulated_payload in manipulation_attempts:
            # Create manipulated token
            manipulated_token = jwt.encode(manipulated_payload, secret_key, algorithm='HS256')
            
            # Attempt access with manipulated token
            async with security_client.authenticated_request(
                manipulated_token, target_org.id
            ) as client:
                response = await client.get('/api/v1/courses')
                
                # Should be blocked due to organization membership validation
                assert response.status_code in [401, 403], \
                    f"Manipulated token should be rejected: {manipulated_payload}"

    async def test_organization_id_injection_attack(self, security_client, attacker_setup):
        """
        Test prevention of organization ID injection attacks
        
        ATTACK SCENARIO:
        Attacker injects malicious organization IDs in headers, URLs, or body
        to bypass organization validation or cause system errors.
        """
        
        attacker_user = attacker_setup['attacker_user']
        attacker_token = generate_valid_jwt_token(attacker_user)
        
        # Injection attack payloads
        injection_payloads = [
            # SQL injection attempts
            "'; DROP TABLE organizations; --",
            "' OR '1'='1",
            "UNION SELECT * FROM users",
            
            # NoSQL injection attempts
            "{'$ne': null}",
            "'; return true; //",
            
            # Path traversal attempts
            "../../../etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            
            # Command injection attempts
            "; rm -rf /",
            "$(whoami)",
            "`id`",
            
            # XSS attempts
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            
            # LDAP injection attempts
            ")(objectClass=*",
            "*)(uid=*))(|(uid=*",
        ]
        
        for payload in injection_payloads:
            # Test header injection
            headers = {'X-Organization-ID': payload}
            
            async with security_client.request_with_headers(
                attacker_token, headers
            ) as client:
                response = await client.get('/api/v1/courses')
                
                # Should reject malicious organization IDs
                assert response.status_code in [400, 403, 422], \
                    f"Injection payload should be rejected: {payload}"
                
                # Response should not contain error details that could aid attacker
                error_response = response.json()
                assert payload not in str(error_response), \
                    "Error response should not echo back injection payload"

    async def test_session_hijacking_prevention(self, security_client, attacker_setup):
        """
        Test prevention of session hijacking between organizations
        
        ATTACK SCENARIO:
        Attacker attempts to hijack session tokens or cookies from
        users in other organizations to gain unauthorized access.
        """
        
        target_admin = attacker_setup['target_admin']
        attacker_user = attacker_setup['attacker_user']
        target_org = attacker_setup['target_org']
        attacker_org = attacker_setup['attacker_org']
        
        # Legitimate admin session
        admin_token = generate_valid_jwt_token(target_admin)
        
        # Simulate session token theft scenario
        # Attacker gets admin token but tries to use it with their own organization context
        async with security_client.authenticated_request(
            admin_token, attacker_org.id  # Wrong organization context
        ) as client:
            response = await client.get('/api/v1/courses')
            
            # Should be blocked due to organization membership validation
            assert response.status_code == 403, \
                "Stolen token with wrong organization context should be rejected"
        
        # Attacker tries to use their token with target organization context
        attacker_token = generate_valid_jwt_token(attacker_user)
        
        async with security_client.authenticated_request(
            attacker_token, target_org.id  # Wrong organization for this user
        ) as client:
            response = await client.get('/api/v1/courses')
            
            # Should be blocked due to organization membership validation
            assert response.status_code == 403, \
                "Valid token with wrong organization context should be rejected"

    async def test_timing_attack_resistance(self, security_client, attacker_setup):
        """
        Test resistance to timing attacks for organization enumeration
        
        ATTACK SCENARIO:
        Attacker measures response times to infer valid organization IDs
        or determine organization membership patterns.
        """
        
        attacker_user = attacker_setup['attacker_user']
        attacker_token = generate_valid_jwt_token(attacker_user)
        
        # Test organization IDs (mix of valid and invalid)
        test_org_ids = [
            attacker_setup['target_org'].id,  # Valid but unauthorized
            attacker_setup['attacker_org'].id,  # Valid and authorized
            str(uuid.uuid4()),  # Invalid UUID
            'nonexistent-org',  # Invalid format
        ]
        
        response_times = {}
        
        for org_id in test_org_ids:
            start_time = datetime.utcnow()
            
            async with security_client.authenticated_request(
                attacker_token, org_id
            ) as client:
                try:
                    response = await client.get('/api/v1/courses')
                    end_time = datetime.utcnow()
                    
                    response_time = (end_time - start_time).total_seconds()
                    response_times[org_id] = {
                        'time': response_time,
                        'status': response.status_code
                    }
                except Exception:
                    end_time = datetime.utcnow()
                    response_time = (end_time - start_time).total_seconds()
                    response_times[org_id] = {
                        'time': response_time,
                        'status': 'error'
                    }
        
        # Analyze timing patterns
        times = [result['time'] for result in response_times.values()]
        max_time = max(times)
        min_time = min(times)
        
        # Response times should be relatively consistent to prevent timing attacks
        time_variance = max_time - min_time
        assert time_variance < 0.5, \
            f"Response time variance too high: {time_variance}s - may allow timing attacks"

    async def test_mass_assignment_attack_prevention(self, security_client, attacker_setup):
        """
        Test prevention of mass assignment attacks on organization data
        
        ATTACK SCENARIO:
        Attacker sends additional fields in requests to modify
        organization membership, roles, or access permissions.
        """
        
        attacker_user = attacker_setup['attacker_user']
        attacker_token = generate_valid_jwt_token(attacker_user)
        target_org = attacker_setup['target_org']
        attacker_org = attacker_setup['attacker_org']
        
        # Course creation with mass assignment attempt
        malicious_course_data = {
            'title': 'Legitimate Course Title',
            'description': 'Normal course description',
            'category': 'programming',
            
            # Mass assignment attempts
            'organization_id': target_org.id,  # Try to assign to different org
            'instructor_id': attacker_setup['target_admin'].id,  # Try to impersonate
            'is_admin_course': True,  # Try to set privileged flag
            'role': 'super_admin',  # Try to escalate privileges
            'permissions': ['admin', 'super_user'],  # Try to grant permissions
            'organization_role': 'admin',  # Try to change organization role
        }
        
        async with security_client.authenticated_request(
            attacker_token, attacker_org.id
        ) as client:
            response = await client.post('/api/v1/courses', json=malicious_course_data)
            
            if response.status_code == 201:
                created_course = response.json()
                
                # Verify mass assignment was ignored
                assert created_course['instructor_id'] == attacker_user.id, \
                    "Mass assignment changed instructor_id"
                
                # Verify course was created in correct organization
                # (This would be validated by checking organization context in actual implementation)
                assert 'organization_id' not in created_course or \
                       created_course.get('organization_id') != target_org.id, \
                    "Mass assignment allowed organization change"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])