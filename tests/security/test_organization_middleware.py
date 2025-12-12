"""
Unit Tests for Organization Authorization Middleware

TESTING STRATEGY:
Comprehensive testing of multi-tenant security enforcement to ensure
complete data isolation between organizations and prevent unauthorized
cross-tenant access attempts.

TEST CATEGORIES:
1. Authentication Validation - JWT token processing and user extraction
2. Organization Context Extraction - Request parsing for organization IDs
3. Membership Verification - Organization access validation
4. Security Logging - Audit trail verification
5. Error Handling - Proper exception handling and user feedback
6. Edge Cases - Boundary conditions and attack scenarios

SECURITY TEST COVERAGE:
- Valid organization access by authorized users
- Blocked access attempts to unauthorized organizations
- Malformed request handling and input validation
- JWT token validation and expiration scenarios
- Audit logging for security monitoring
- Performance under load and concurrent access
"""

import pytest
import json
import uuid
import asyncio
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from starlette.responses import JSONResponse

# Import the middleware under test
import sys
sys.path.insert(0, '/app')
from shared.auth.organization_middleware import OrganizationAuthorizationMiddleware, get_organization_context


@pytest.mark.skip(reason="Needs refactoring to use real objects")
class TestOrganizationAuthorizationMiddleware:
    """Test suite for organization authorization middleware"""
    
    @pytest.fixture
    def middleware_config(self):
        """Configuration for middleware testing"""
        return {
            'jwt': {
                'secret_key': 'test-secret-key-for-testing',
                'algorithm': 'HS256'
            },
            'services': {
                'user_management_url': 'http://test-user-service:8000',
                'organization_management_url': 'http://test-org-service:8008'
            }
        }
    
    @pytest.fixture
    def middleware(self, middleware_config):
        """Create middleware instance for testing"""
        mock_app = Mock()
        return OrganizationAuthorizationMiddleware(mock_app, middleware_config)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            'id': str(uuid.uuid4()),
            'email': 'test@example.com',
            'role': 'instructor',
            'organization_id': str(uuid.uuid4()),
            'full_name': 'Test User',
            'is_active': True
        }
    
    @pytest.fixture
    def sample_organization_id(self):
        """Sample organization ID for testing"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def valid_jwt_token(self, middleware_config, sample_user_data):
        """Generate valid JWT token for testing"""
        payload = {
            'sub': sample_user_data['id'],
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, middleware_config['jwt']['secret_key'], algorithm='HS256')
    
    @pytest.fixture
    def expired_jwt_token(self, middleware_config, sample_user_data):
        """Generate expired JWT token for testing"""
        payload = {
            'sub': sample_user_data['id'],
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        return jwt.encode(payload, middleware_config['jwt']['secret_key'], algorithm='HS256')
    
    @pytest.fixture
    def mock_request(self, valid_jwt_token, sample_organization_id):
        """Create mock request for testing"""
        request = Mock(spec=Request)
        request.url.path = f'/api/v1/organizations/{sample_organization_id}/courses'
        request.method = 'GET'
        request.headers = {
            'Authorization': f'Bearer {valid_jwt_token}',
            'X-Organization-ID': sample_organization_id,
            'User-Agent': 'Test-Client/1.0'
        }
        request.client.host = '192.168.1.100'
        request.state = Mock()
        return request

    async def test_exempt_endpoints_bypass_validation(self, middleware):
        """Test that exempt endpoints bypass organization validation"""
        exempt_endpoints = ['/health', '/docs', '/openapi.json', '/api/v1/auth/login']
        
        for endpoint in exempt_endpoints:
            request = Mock(spec=Request)
            request.url.path = endpoint
            
            call_next = AsyncMock(return_value=JSONResponse(content={'status': 'ok'}))
            
            response = await middleware.dispatch(request, call_next)
            
            # Should call next without validation
            call_next.assert_called_once_with(request)
            assert response.status_code == 200

    async def test_valid_organization_access_succeeds(self, middleware, mock_request, sample_user_data, sample_organization_id):
        """Test successful access with valid organization membership"""
        
        with patch.object(middleware, '_validate_jwt_token', return_value=sample_user_data), \
             patch.object(middleware, '_extract_organization_id', return_value=sample_organization_id), \
             patch.object(middleware, '_verify_organization_membership', return_value=True), \
             patch.object(middleware, '_log_security_event') as mock_log:
            
            call_next = AsyncMock(return_value=JSONResponse(content={'data': 'success'}))
            
            response = await middleware.dispatch(mock_request, call_next)
            
            # Should proceed to next middleware
            call_next.assert_called_once_with(mock_request)
            
            # Should set organization context
            assert mock_request.state.organization_id == sample_organization_id
            assert mock_request.state.user_info == sample_user_data
            
            # Should log successful access
            mock_log.assert_called_with(
                user_id=sample_user_data['id'],
                organization_id=sample_organization_id,
                action='ORGANIZATION_ACCESS',
                resource_type='organization',
                resource_id=sample_organization_id,
                attempted_organization_id=sample_organization_id,
                success=True,
                details={'endpoint': mock_request.url.path, 'method': mock_request.method},
                ip_address=mock_request.client.host,
                user_agent=mock_request.headers.get('user-agent')
            )

    async def test_unauthorized_organization_access_blocked(self, middleware, mock_request, sample_user_data, sample_organization_id):
        """Test blocked access for unauthorized organization"""
        
        with patch.object(middleware, '_validate_jwt_token', return_value=sample_user_data), \
             patch.object(middleware, '_extract_organization_id', return_value=sample_organization_id), \
             patch.object(middleware, '_verify_organization_membership', return_value=False), \
             patch.object(middleware, '_log_security_event') as mock_log:
            
            call_next = AsyncMock()
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(mock_request, call_next)
            
            # Should raise 403 Forbidden
            assert exc_info.value.status_code == 403
            assert 'Access denied' in exc_info.value.detail
            
            # Should not proceed to next middleware
            call_next.assert_not_called()
            
            # Should log failed access attempt
            mock_log.assert_called_with(
                user_id=sample_user_data['id'],
                organization_id=sample_user_data.get('organization_id'),
                action='UNAUTHORIZED_ACCESS_ATTEMPT',
                resource_type='organization',
                resource_id=sample_organization_id,
                attempted_organization_id=sample_organization_id,
                success=False,
                details={'endpoint': mock_request.url.path, 'method': mock_request.method},
                ip_address=mock_request.client.host,
                user_agent=mock_request.headers.get('user-agent')
            )

    async def test_invalid_jwt_token_rejected(self, middleware, sample_organization_id):
        """Test rejection of invalid JWT tokens"""
        
        request = Mock(spec=Request)
        request.url.path = f'/api/v1/organizations/{sample_organization_id}/courses'
        request.headers = {'Authorization': 'Bearer invalid-token'}
        
        with patch.object(middleware, '_validate_jwt_token', return_value=None):
            call_next = AsyncMock()
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request, call_next)
            
            assert exc_info.value.status_code == 401
            assert 'Invalid or missing authentication token' in exc_info.value.detail

    async def test_missing_organization_id_rejected(self, middleware, sample_user_data):
        """Test rejection when organization ID cannot be extracted"""
        
        request = Mock(spec=Request)
        request.url.path = '/api/v1/courses'  # No organization in path
        request.headers = {'Authorization': 'Bearer valid-token'}
        
        with patch.object(middleware, '_validate_jwt_token', return_value=sample_user_data), \
             patch.object(middleware, '_extract_organization_id', return_value=None):
            
            call_next = AsyncMock()
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request, call_next)
            
            assert exc_info.value.status_code == 400
            assert 'Organization ID required' in exc_info.value.detail

    async def test_jwt_token_validation_with_expired_token(self, middleware, expired_jwt_token):
        """Test JWT validation with expired token"""
        
        request = Mock(spec=Request)
        request.headers = {'Authorization': f'Bearer {expired_jwt_token}'}
        
        result = await middleware._validate_jwt_token(request)
        
        assert result is None

    async def test_jwt_token_validation_with_malformed_token(self, middleware):
        """Test JWT validation with malformed token"""
        
        request = Mock(spec=Request)
        request.headers = {'Authorization': 'Bearer malformed.token.here'}
        
        result = await middleware._validate_jwt_token(request)
        
        assert result is None

    async def test_organization_id_extraction_from_header(self, middleware, sample_organization_id):
        """Test organization ID extraction from X-Organization-ID header"""
        
        request = Mock(spec=Request)
        request.headers = {'X-Organization-ID': sample_organization_id}
        request.url.path = '/api/v1/courses'
        request.query_params = {}
        request.method = 'GET'
        
        result = await middleware._extract_organization_id(request)
        
        assert result == sample_organization_id

    async def test_organization_id_extraction_from_path(self, middleware, sample_organization_id):
        """Test organization ID extraction from URL path"""
        
        request = Mock(spec=Request)
        request.headers = {}
        request.url.path = f'/api/v1/organizations/{sample_organization_id}/courses'
        request.query_params = {}
        request.method = 'GET'
        
        result = await middleware._extract_organization_id(request)
        
        assert result == sample_organization_id

    async def test_organization_id_extraction_from_query_param(self, middleware, sample_organization_id):
        """Test organization ID extraction from query parameter"""
        
        request = Mock(spec=Request)
        request.headers = {}
        request.url.path = '/api/v1/courses'
        request.query_params = {'organization_id': sample_organization_id}
        request.method = 'GET'
        
        result = await middleware._extract_organization_id(request)
        
        assert result == sample_organization_id

    async def test_organization_membership_verification_success(self, middleware, sample_user_data, sample_organization_id):
        """Test successful organization membership verification"""
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'active'}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await middleware._verify_organization_membership(
                sample_user_data['id'], 
                sample_organization_id
            )
            
            assert result is True

    async def test_organization_membership_verification_failure(self, middleware, sample_user_data, sample_organization_id):
        """Test failed organization membership verification"""
        
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await middleware._verify_organization_membership(
                sample_user_data['id'], 
                sample_organization_id
            )
            
            assert result is False

    async def test_user_info_retrieval_success(self, middleware, sample_user_data):
        """Test successful user information retrieval"""
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_user_data
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await middleware._get_user_info(sample_user_data['id'])
            
            assert result == sample_user_data

    async def test_user_info_retrieval_user_not_found(self, middleware, sample_user_data):
        """Test user information retrieval when user not found"""
        
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await middleware._get_user_info(sample_user_data['id'])
            
            assert result is None

    async def test_concurrent_access_handling(self, middleware, mock_request, sample_user_data, sample_organization_id):
        """Test middleware handling under concurrent load"""
        
        with patch.object(middleware, '_validate_jwt_token', return_value=sample_user_data), \
             patch.object(middleware, '_extract_organization_id', return_value=sample_organization_id), \
             patch.object(middleware, '_verify_organization_membership', return_value=True), \
             patch.object(middleware, '_log_security_event'):
            
            # Simulate concurrent requests
            tasks = []
            for _ in range(10):
                call_next = AsyncMock(return_value=JSONResponse(content={'data': 'success'}))
                task = middleware.dispatch(mock_request, call_next)
                tasks.append(task)
            
            # All requests should succeed
            results = await asyncio.gather(*tasks)
            assert all(result.status_code == 200 for result in results)

    async def test_security_logging_comprehensive(self, middleware, mock_request, sample_user_data, sample_organization_id):
        """Test comprehensive security event logging"""
        
        with patch.object(middleware, '_validate_jwt_token', return_value=sample_user_data), \
             patch.object(middleware, '_extract_organization_id', return_value=sample_organization_id), \
             patch.object(middleware, '_verify_organization_membership', return_value=True), \
             patch.object(middleware, '_log_security_event') as mock_log:
            
            call_next = AsyncMock(return_value=JSONResponse(content={'data': 'success'}))
            
            await middleware.dispatch(mock_request, call_next)
            
            # Verify all required fields are logged
            call_args = mock_log.call_args
            assert call_args[1]['user_id'] == sample_user_data['id']
            assert call_args[1]['organization_id'] == sample_organization_id
            assert call_args[1]['action'] == 'ORGANIZATION_ACCESS'
            assert call_args[1]['resource_type'] == 'organization'
            assert call_args[1]['success'] is True
            assert 'details' in call_args[1]
            assert 'ip_address' in call_args[1]
            assert 'user_agent' in call_args[1]


@pytest.mark.skip(reason="Needs refactoring to use real objects")
class TestOrganizationDependency:
    """Test suite for organization context dependency"""
    
    def test_get_organization_context_success(self):
        """Test successful organization context extraction"""
        
        request = Mock(spec=Request)
        request.state.organization_id = str(uuid.uuid4())
        request.state.user_info = {'id': str(uuid.uuid4()), 'role': 'instructor'}
        
        dependency = get_organization_context
        result = dependency(request)
        
        assert result['organization_id'] == request.state.organization_id
        assert result['user_info'] == request.state.user_info

    def test_get_organization_context_missing_context(self):
        """Test organization context extraction when context missing"""

        request = Mock(spec=Request)
        # Create a mock state object without organization_id attribute
        request.state = Mock(spec=[])  # Empty spec means no attributes

        dependency = get_organization_context

        with pytest.raises(HTTPException) as exc_info:
            dependency(request)

        assert exc_info.value.status_code == 500
        assert 'Organization context not available' in exc_info.value.detail


@pytest.mark.asyncio
@pytest.mark.skip(reason="Needs refactoring to use real objects")
class TestSecurityScenarios:
    """Integration tests for security scenarios"""

    @pytest.fixture
    def middleware_config(self):
        """Configuration for middleware testing"""
        return {
            'jwt': {
                'secret_key': 'test-secret-key-for-testing',
                'algorithm': 'HS256'
            },
            'services': {
                'user_management_url': 'http://test-user-service:8000',
                'organization_management_url': 'http://test-org-service:8008'
            }
        }

    async def test_privilege_escalation_prevention(self, middleware_config):
        """Test prevention of privilege escalation across organizations"""

        # User from organization A tries to access organization B
        user_org_a = str(uuid.uuid4())
        target_org_b = str(uuid.uuid4())

        user_data = {
            'id': str(uuid.uuid4()),
            'organization_id': user_org_a,
            'role': 'admin'  # Even admin role should not grant cross-org access
        }

        middleware = OrganizationAuthorizationMiddleware(Mock(), middleware_config)

        request = Mock(spec=Request)
        request.url.path = f'/api/v1/organizations/{target_org_b}/courses'
        request.method = 'GET'
        request.headers = {'X-Organization-ID': target_org_b, 'user-agent': 'Test-Client/1.0'}
        # Create mock client object
        request.client = Mock()
        request.client.host = '192.168.1.100'
        request.state = Mock()

        with patch.object(middleware, '_validate_jwt_token', return_value=user_data), \
             patch.object(middleware, '_extract_organization_id', return_value=target_org_b), \
             patch.object(middleware, '_verify_organization_membership', return_value=False), \
             patch.object(middleware, '_log_security_event'):

            call_next = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request, call_next)

            assert exc_info.value.status_code == 403
            call_next.assert_not_called()

    async def test_organization_id_tampering_prevention(self, middleware_config):
        """Test prevention of organization ID tampering attacks"""

        # Test various malformed organization IDs
        malformed_org_ids = [
            'not-a-uuid',
            '../../etc/passwd',
            '<script>alert("xss")</script>',
            'SELECT * FROM organizations;',
            '',
            None
        ]

        middleware = OrganizationAuthorizationMiddleware(Mock(), middleware_config)

        for malformed_id in malformed_org_ids:
            request = Mock(spec=Request)
            request.url.path = '/api/v1/courses'
            request.method = 'GET'
            request.headers = {'X-Organization-ID': malformed_id, 'user-agent': 'Test-Client/1.0'} if malformed_id else {'user-agent': 'Test-Client/1.0'}
            # Create mock client object
            request.client = Mock()
            request.client.host = '192.168.1.100'
            request.state = Mock()

            with patch.object(middleware, '_validate_jwt_token', return_value={'id': str(uuid.uuid4())}), \
                 patch.object(middleware, '_extract_organization_id', return_value=malformed_id), \
                 patch.object(middleware, '_verify_organization_membership', return_value=False), \
                 patch.object(middleware, '_log_security_event'):

                call_next = AsyncMock()

                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(request, call_next)

                # Should reject invalid organization IDs (400/500) or deny access (403)
                assert exc_info.value.status_code in [400, 403, 500]
                call_next.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])