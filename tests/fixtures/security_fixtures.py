"""
Security Test Fixtures for Multi-Tenant Testing

FIXTURE STRATEGY:
Provides comprehensive test fixtures for security testing including
organization setup, user creation, authentication tokens, and
specialized test clients for security boundary validation.

FIXTURE CATEGORIES:
1. Organization Fixtures - Test organizations with proper isolation
2. User Fixtures - Users across organizations with different roles
3. Authentication Fixtures - JWT tokens and session management
4. Test Client Fixtures - Security-aware HTTP clients
5. Data Fixtures - Test data scoped to organizations

SECURITY TESTING SUPPORT:
- Organization boundary validation
- Cross-tenant access prevention
- Role-based access control testing
- Authentication and authorization flows
- Cache and database isolation verification
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

import jwt
import httpx
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock


@dataclass
class OrganizationFixture:
    """Test organization fixture"""
    id: str
    name: str
    slug: str
    created_at: datetime
    settings: Dict[str, Any]
    
    @classmethod
    def create(cls, name: str, slug: str, **kwargs):
        """Create organization fixture with defaults"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            created_at=datetime.utcnow(),
            settings=kwargs.get('settings', {})
        )


@dataclass 
class UserFixture:
    """Test user fixture"""
    id: str
    email: str
    role: str
    organization_id: str
    full_name: str
    is_active: bool
    created_at: datetime
    
    @classmethod
    def create(cls, email: str, role: str, organization_id: str, **kwargs):
        """Create user fixture with defaults"""
        return cls(
            id=str(uuid.uuid4()),
            email=email,
            role=role,
            organization_id=organization_id,
            full_name=kwargs.get('full_name', f'Test User {email}'),
            is_active=kwargs.get('is_active', True),
            created_at=datetime.utcnow()
        )


def create_test_organizations(org_configs: List[Dict[str, Any]]) -> List[OrganizationFixture]:
    """
    Create multiple test organizations for isolation testing
    
    Args:
        org_configs: List of organization configuration dictionaries
        
    Returns:
        List of OrganizationFixture instances
    """
    organizations = []
    
    for config in org_configs:
        org = OrganizationFixture.create(
            name=config['name'],
            slug=config['slug'],
            settings=config.get('settings', {})
        )
        organizations.append(org)
    
    return organizations


def create_test_users(user_configs: List[Dict[str, Any]]) -> List[UserFixture]:
    """
    Create multiple test users across organizations
    
    Args:
        user_configs: List of user configuration dictionaries
        
    Returns:
        List of UserFixture instances
    """
    users = []
    
    for config in user_configs:
        user = UserFixture.create(
            email=config['email'],
            role=config['role'],
            organization_id=config['organization_id'],
            full_name=config.get('full_name'),
            is_active=config.get('is_active', True)
        )
        users.append(user)
    
    return users


def generate_valid_jwt_token(
    user: UserFixture,
    secret_key: str = 'test-secret-key-for-testing',
    expiry_hours: int = 1
) -> str:
    """
    Generate valid JWT token for test user
    
    Args:
        user: User fixture
        secret_key: JWT secret key
        expiry_hours: Token expiry in hours
        
    Returns:
        JWT token string
    """
    payload = {
        'sub': user.id,
        'email': user.email,
        'role': user.role,
        'organization_id': user.organization_id,
        'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, secret_key, algorithm='HS256')


def generate_expired_jwt_token(
    user: UserFixture,
    secret_key: str = 'test-secret-key-for-testing'
) -> str:
    """
    Generate expired JWT token for testing expiry scenarios
    
    Args:
        user: User fixture
        secret_key: JWT secret key
        
    Returns:
        Expired JWT token string
    """
    payload = {
        'sub': user.id,
        'email': user.email,
        'role': user.role,
        'organization_id': user.organization_id,
        'exp': datetime.utcnow() - timedelta(hours=1),
        'iat': datetime.utcnow() - timedelta(hours=2)
    }
    
    return jwt.encode(payload, secret_key, algorithm='HS256')


def generate_malformed_jwt_token() -> str:
    """Generate malformed JWT token for testing token validation"""
    return 'malformed.jwt.token.here'


class SecurityTestClient:
    """
    Test client with security-aware features for organization boundary testing
    
    Provides authenticated requests with proper organization context
    and validation of security boundaries.
    """
    
    def __init__(self, base_url: str = 'http://testserver'):
        self.base_url = base_url
        self.client = TestClient(app=None)  # Would be replaced with actual app in real tests
    
    @asynccontextmanager
    async def authenticated_request(self, jwt_token: str, organization_id: str):
        """
        Create authenticated request context with organization validation
        
        Args:
            jwt_token: Valid JWT token for authentication
            organization_id: Organization ID for request context
            
        Yields:
            HTTP client with authentication and organization headers
        """
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'X-Organization-ID': organization_id,
            'Content-Type': 'application/json'
        }
        
        # Mock client that simulates organization middleware behavior
        mock_client = MockSecurityClient(headers, organization_id)
        
        try:
            yield mock_client
        finally:
            # Cleanup if needed
            pass
    
    @asynccontextmanager
    async def request_with_headers(self, jwt_token: str, custom_headers: Dict[str, str]):
        """
        Create request context with custom headers for testing injection attacks
        
        Args:
            jwt_token: JWT token for authentication
            custom_headers: Custom headers to include
            
        Yields:
            HTTP client with custom headers
        """
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json',
            **custom_headers
        }
        
        mock_client = MockSecurityClient(headers)
        
        try:
            yield mock_client
        finally:
            pass


class MockSecurityClient:
    """
    Mock HTTP client that simulates security middleware behavior
    
    Simulates the organization authorization middleware and validates
    requests according to security policies for testing purposes.
    """
    
    def __init__(self, headers: Dict[str, str], organization_id: Optional[str] = None):
        self.headers = headers
        self.organization_id = organization_id
        self._simulate_middleware_validation()
    
    def _simulate_middleware_validation(self):
        """Simulate organization middleware validation"""
        # Extract JWT token
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            self.auth_valid = False
            return
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode JWT to extract user's organization
            payload = jwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
            self.user_org_id = payload.get('organization_id')
            
            # Simulate successful auth
            self.auth_valid = True
            
            # Simulate organization membership validation
            org_id = self.headers.get('X-Organization-ID')
            if org_id and self.user_org_id:
                # Check if user belongs to the organization being accessed
                self.org_access_valid = (org_id == self.user_org_id)
            else:
                self.org_access_valid = False
                
        except Exception:
            self.auth_valid = False
            self.org_access_valid = False
            self.user_org_id = None
    
    async def get(self, url: str, **kwargs) -> 'MockResponse':
        """Mock GET request with security validation"""
        return self._make_request('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> 'MockResponse':
        """Mock POST request with security validation"""
        return self._make_request('POST', url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> 'MockResponse':
        """Mock PUT request with security validation"""
        return self._make_request('PUT', url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> 'MockResponse':
        """Mock DELETE request with security validation"""
        return self._make_request('DELETE', url, **kwargs)
    
    def _make_request(self, method: str, url: str, **kwargs) -> 'MockResponse':
        """
        Simulate request with security validation
        
        Returns appropriate HTTP status codes based on security validation
        """
        # Check authentication
        if not self.auth_valid:
            return MockResponse(401, {'detail': 'Invalid or missing authentication token'})
        
        # Check organization access for non-exempt endpoints
        exempt_endpoints = ['/health', '/docs', '/api/v1/auth/']
        is_exempt = any(url.startswith(endpoint) for endpoint in exempt_endpoints)
        
        if not is_exempt:
            org_id = self.headers.get('X-Organization-ID')
            
            # Check if organization ID is required
            if not org_id:
                return MockResponse(400, {'detail': 'Organization ID required for this operation'})
            
            # Validate organization ID format
            try:
                uuid.UUID(org_id)
            except ValueError:
                return MockResponse(400, {'detail': 'Invalid organization ID format'})
            
            # Check organization membership using JWT validation
            if not self.org_access_valid:
                return MockResponse(403, {'detail': f'Access denied: User not authorized for organization {org_id}'})
        
        # Simulate successful request
        if method == 'GET':
            if 'courses' in url:
                return MockResponse(200, [
                    {
                        'id': str(uuid.uuid4()),
                        'title': 'Test Course',
                        'organization_id': self.organization_id
                    }
                ])
            elif 'analytics' in url:
                return MockResponse(200, {
                    'organization_id': self.organization_id,
                    'total_courses': 5,
                    'total_students': 50
                })
            else:
                return MockResponse(200, {'status': 'success'})
        
        elif method == 'POST':
            if 'courses' in url:
                return MockResponse(201, {
                    'id': str(uuid.uuid4()),
                    'title': kwargs.get('json', {}).get('title', 'Test Course'),
                    'instructor_id': 'test-instructor-id',
                    'organization_id': self.organization_id
                })
            elif 'enrollments' in url:
                return MockResponse(201, {
                    'id': str(uuid.uuid4()),
                    'status': 'enrolled'
                })
            else:
                return MockResponse(201, {'status': 'created'})
        
        elif method in ['PUT', 'DELETE']:
            return MockResponse(200, {'status': 'success'})
        
        return MockResponse(200, {'status': 'success'})


class MockResponse:
    """Mock HTTP response for testing"""
    
    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data
    
    def json(self) -> Any:
        """Return response data as JSON"""
        return self._data
    
    def text(self) -> str:
        """Return response data as text"""
        return json.dumps(self._data)


# Test data generators
def create_test_course_data(organization_id: str, **kwargs) -> Dict[str, Any]:
    """Create test course data scoped to organization"""
    return {
        'id': str(uuid.uuid4()),
        'title': kwargs.get('title', 'Test Course'),
        'description': kwargs.get('description', 'Test course description'),
        'instructor_id': kwargs.get('instructor_id', str(uuid.uuid4())),
        'organization_id': organization_id,
        'category': kwargs.get('category', 'programming'),
        'difficulty_level': kwargs.get('difficulty_level', 'beginner'),
        'estimated_duration': kwargs.get('estimated_duration', 8),
        'duration_unit': kwargs.get('duration_unit', 'weeks'),
        'is_published': kwargs.get('is_published', False),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }


def create_test_enrollment_data(student_id: str, course_id: str, organization_id: str) -> Dict[str, Any]:
    """Create test enrollment data scoped to organization"""
    return {
        'id': str(uuid.uuid4()),
        'student_id': student_id,
        'course_id': course_id,
        'organization_id': organization_id,
        'enrollment_status': 'enrolled',
        'enrolled_at': datetime.utcnow().isoformat(),
        'progress_percentage': 0.0
    }


def create_test_analytics_data(organization_id: str) -> Dict[str, Any]:
    """Create test analytics data scoped to organization"""
    return {
        'organization_id': organization_id,
        'total_courses': 15,
        'total_students': 245,
        'total_instructors': 8,
        'active_enrollments': 180,
        'completed_courses': 65,
        'average_completion_rate': 78.5,
        'generated_at': datetime.utcnow().isoformat()
    }


# Security validation helpers
def validate_organization_isolation(data: Any, expected_org_id: str) -> bool:
    """
    Validate that data is properly isolated to expected organization
    
    Args:
        data: Data to validate
        expected_org_id: Expected organization ID
        
    Returns:
        True if data is properly isolated, False otherwise
    """
    if isinstance(data, dict):
        org_id = data.get('organization_id')
        return org_id == expected_org_id
    
    elif isinstance(data, list):
        return all(validate_organization_isolation(item, expected_org_id) for item in data)
    
    return True  # Non-organization data


def assert_no_cross_organization_data(data: Any, forbidden_org_ids: List[str]) -> None:
    """
    Assert that data contains no information from forbidden organizations
    
    Args:
        data: Data to validate
        forbidden_org_ids: List of organization IDs that should not appear
        
    Raises:
        AssertionError: If forbidden organization data is found
    """
    if isinstance(data, dict):
        org_id = data.get('organization_id')
        assert org_id not in forbidden_org_ids, \
            f"Found forbidden organization data: {org_id}"
        
        # Check nested dictionaries
        for value in data.values():
            if isinstance(value, (dict, list)):
                assert_no_cross_organization_data(value, forbidden_org_ids)
    
    elif isinstance(data, list):
        for item in data:
            assert_no_cross_organization_data(item, forbidden_org_ids)


# Performance testing helpers
class SecurityPerformanceTracker:
    """Track performance metrics for security operations"""
    
    def __init__(self):
        self.operation_times = {}
        self.operation_counts = {}
    
    def record_operation(self, operation: str, duration: float):
        """Record operation timing"""
        if operation not in self.operation_times:
            self.operation_times[operation] = []
            self.operation_counts[operation] = 0
        
        self.operation_times[operation].append(duration)
        self.operation_counts[operation] += 1
    
    def get_average_time(self, operation: str) -> float:
        """Get average time for operation"""
        times = self.operation_times.get(operation, [])
        return sum(times) / len(times) if times else 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {}
        
        for operation in self.operation_times:
            times = self.operation_times[operation]
            report[operation] = {
                'count': self.operation_counts[operation],
                'average_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'total_time': sum(times)
            }
        
        return report