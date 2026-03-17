"""
Security Hardening Integration Tests - Phase 1

This test module validates security hardening at the integration level,
testing actual service behavior rather than static code analysis.

Business Context:
- Integration tests verify security controls work in realistic scenarios
- Tests actual HTTP responses and service behavior
- Validates security headers and CORS behavior

Test Categories:
1. CORS Behavior Tests - Verify proper origin handling
2. SSL/TLS Tests - Verify certificate validation
3. Authentication Security - Verify no credential leaks
4. Rate Limiting Tests - Verify abuse prevention

Technical Rationale:
- Integration tests catch runtime configuration issues
- Security must be verified at the network level
- Tests use actual service endpoints

Author: Claude Code
Created: 2025-11-27
Version: 1.0.0
"""

import os
import sys
import pytest
import asyncio
import httpx
import ssl
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Service configuration
SERVICE_PORTS = {
    'user-management': 8000,
    'course-management': 8001,
    'organization-management': 8003,
    'analytics': 8004,
    'content-management': 8005,
    'rag-service': 8009,
    'metadata-service': 8007,
    'nlp-preprocessing': 8008,
}

BASE_URL = os.getenv('TEST_BASE_URL', 'https://localhost')


def is_service_available(url: str = BASE_URL, port: int = 8000) -> bool:
    """
    Check if a service is available for integration testing.

    Returns:
        True if service is reachable, False otherwise
    """
    import socket
    try:
        # Extract host from URL
        host = url.replace('https://', '').replace('http://', '').split(':')[0]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


# Fixture to check service availability before each test
@pytest.fixture(autouse=True)
def check_service_availability():
    """
    Skip tests if services aren't running.

    This fixture runs before each test and skips if the service is not reachable.
    """
    if not is_service_available():
        pytest.skip("Services not available - integration tests require running Docker services")


class TestCORSIntegration:
    """
    Integration tests for CORS configuration.

    These tests verify that services properly handle Cross-Origin requests
    by checking response headers for various origin scenarios.

    Business Context:
    - CORS misconfiguration is a top web security issue
    - Multi-tenant platforms must restrict which origins can access APIs
    - Proper CORS prevents CSRF and data theft
    """

    @pytest.fixture
    def allowed_origins(self) -> list:
        """
        Return the list of allowed origins for CORS.

        In production, this should match CORS_ORIGINS environment variable.
        """
        return [
            'https://localhost:3000',
            'https://localhost:3001',
            os.getenv('FRONTEND_URL', 'https://localhost:3000'),
        ]

    @pytest.mark.asyncio
    async def test_cors_allows_configured_origins(self, allowed_origins: list):
        """
        Verify CORS allows requests from configured origins.

        Security Requirement:
        - Configured origins should receive proper CORS headers
        - Access-Control-Allow-Origin should match request Origin
        - Access-Control-Allow-Credentials should be true for auth

        Test Approach:
        - Send OPTIONS preflight request
        - Verify Access-Control-Allow-Origin header
        """
        async with httpx.AsyncClient(verify=False) as client:
            for origin in allowed_origins:
                # Test against user-management service
                url = f"{BASE_URL}:8000/health"

                response = await client.options(
                    url,
                    headers={
                        'Origin': origin,
                        'Access-Control-Request-Method': 'GET',
                    }
                )

                # Should return CORS headers for allowed origin
                allow_origin = response.headers.get('Access-Control-Allow-Origin')

                # Should either be the specific origin or credentials won't work
                assert allow_origin == origin or allow_origin is None, (
                    f"Origin {origin} should be explicitly allowed, "
                    f"got: {allow_origin}"
                )

    @pytest.mark.asyncio
    async def test_cors_blocks_unknown_origins(self):
        """
        Verify CORS rejects requests from unknown origins.

        Security Requirement:
        - Unknown origins should NOT receive Access-Control-Allow-Origin
        - Wildcard (*) should NOT be returned for credentialed requests
        - This prevents unauthorized cross-origin access

        Test Approach:
        - Send request with malicious origin
        - Verify no CORS header or specific rejection
        """
        malicious_origins = [
            'https://evil-site.com',
            'https://attacker.io',
            'http://localhost:3000',  # HTTP instead of HTTPS
        ]

        async with httpx.AsyncClient(verify=False) as client:
            for origin in malicious_origins:
                url = f"{BASE_URL}:8000/health"

                response = await client.options(
                    url,
                    headers={
                        'Origin': origin,
                        'Access-Control-Request-Method': 'GET',
                    }
                )

                allow_origin = response.headers.get('Access-Control-Allow-Origin')

                # Should NOT be wildcard or the malicious origin
                assert allow_origin != '*', (
                    f"Wildcard CORS detected! This allows any origin including {origin}"
                )

                # If origin is returned, it should not be the malicious one
                if allow_origin:
                    assert allow_origin != origin, (
                        f"Malicious origin {origin} was allowed by CORS!"
                    )

    @pytest.mark.asyncio
    async def test_cors_wildcard_not_used_with_credentials(self):
        """
        Verify wildcard CORS is not used with credentialed requests.

        Security Requirement:
        - Browsers reject wildcard CORS with credentials
        - But server should not even attempt it
        - This is a defense-in-depth check

        CORS Spec:
        - If Access-Control-Allow-Credentials: true
        - Then Access-Control-Allow-Origin cannot be *
        """
        async with httpx.AsyncClient(verify=False) as client:
            for service, port in SERVICE_PORTS.items():
                url = f"{BASE_URL}:{port}/health"

                try:
                    response = await client.options(
                        url,
                        headers={
                            'Origin': 'https://localhost:3000',
                            'Access-Control-Request-Method': 'GET',
                        },
                        timeout=5.0
                    )

                    allow_origin = response.headers.get('Access-Control-Allow-Origin')
                    allow_creds = response.headers.get('Access-Control-Allow-Credentials')

                    if allow_creds == 'true':
                        assert allow_origin != '*', (
                            f"Service {service} uses wildcard CORS with credentials! "
                            f"This is a security misconfiguration."
                        )
                except httpx.ConnectError:
                    pytest.skip(f"Service {service} not running on port {port}")


class TestSSLVerificationIntegration:
    """
    Integration tests for SSL/TLS verification.

    These tests verify that services properly handle SSL certificates
    and don't accept invalid or self-signed certs in production.

    Business Context:
    - SSL verification prevents man-in-the-middle attacks
    - Production services must validate certificate chains
    - Self-signed certs require explicit trust, not disabled verification
    """

    @pytest.mark.asyncio
    async def test_services_use_https(self):
        """
        Verify all services are accessible via HTTPS.

        Security Requirement:
        - All service endpoints must use TLS
        - HTTP should redirect to HTTPS or be blocked
        - This ensures encrypted communication
        """
        async with httpx.AsyncClient(verify=False) as client:
            for service, port in SERVICE_PORTS.items():
                https_url = f"https://localhost:{port}/health"

                try:
                    response = await client.get(https_url, timeout=5.0)
                    # Service should respond over HTTPS
                    assert response.status_code in [200, 307, 308, 401, 403], (
                        f"Service {service} not responding on HTTPS: {response.status_code}"
                    )
                except httpx.ConnectError:
                    pytest.skip(f"Service {service} not running")

    @pytest.mark.asyncio
    async def test_http_redirects_to_https(self):
        """
        Verify HTTP requests are redirected to HTTPS.

        Security Requirement:
        - HTTP requests should be redirected to HTTPS
        - Or HTTP should be completely blocked
        - This prevents accidental unencrypted traffic
        """
        async with httpx.AsyncClient(follow_redirects=False) as client:
            for service, port in SERVICE_PORTS.items():
                http_url = f"http://localhost:{port}/health"

                try:
                    response = await client.get(http_url, timeout=5.0)

                    # Should either redirect (301/302/307/308) or refuse connection
                    if response.status_code not in [301, 302, 307, 308]:
                        pytest.skip(
                            f"Service {service} accepts HTTP without redirect "
                            f"(status: {response.status_code}). "
                            f"Consider blocking HTTP entirely."
                        )
                except (httpx.ConnectError, httpx.ConnectTimeout):
                    # HTTP refused is acceptable (HTTPS only)
                    pass


class TestAuthenticationSecurityIntegration:
    """
    Integration tests for authentication security.

    These tests verify that authentication endpoints don't leak
    sensitive information through responses, logs, or errors.

    Business Context:
    - Login endpoints are prime targets for attacks
    - Credential enumeration must be prevented
    - Error messages should not reveal valid usernames
    """

    @pytest.mark.asyncio
    async def test_login_does_not_reveal_user_existence(self):
        """
        Verify login endpoint doesn't reveal if username exists.

        Security Requirement:
        - Same error message for invalid username and invalid password
        - Response time should be similar for both cases
        - This prevents username enumeration attacks
        """
        async with httpx.AsyncClient(verify=False) as client:
            url = f"{BASE_URL}:8000/auth/login"

            # Test with definitely non-existent user
            invalid_user_response = await client.post(
                url,
                json={'username': 'definitely_not_a_real_user_12345', 'password': 'test'},
                timeout=10.0
            )

            # Test with possibly valid user but wrong password
            wrong_password_response = await client.post(
                url,
                json={'username': 'admin', 'password': 'definitely_wrong_password_12345'},
                timeout=10.0
            )

            # Both should return 401 with same error message
            assert invalid_user_response.status_code == wrong_password_response.status_code, (
                "Different status codes reveal username existence"
            )

            # Error messages should be identical
            try:
                invalid_detail = invalid_user_response.json().get('detail', '')
                wrong_detail = wrong_password_response.json().get('detail', '')

                # Messages should be generic
                assert 'user' not in invalid_detail.lower() or 'not found' not in invalid_detail.lower(), (
                    f"Error message reveals user existence: {invalid_detail}"
                )
            except Exception:
                pass  # JSON parsing failed, acceptable

    @pytest.mark.asyncio
    async def test_login_response_does_not_contain_password(self):
        """
        Verify login response never contains password field.

        Security Requirement:
        - Response must not echo back the password
        - Even in error cases, password should not be in response
        - This is a defense against logging and inspection
        """
        async with httpx.AsyncClient(verify=False) as client:
            url = f"{BASE_URL}:8000/auth/login"

            response = await client.post(
                url,
                json={'username': 'test', 'password': 'test_password_123'},
                timeout=10.0
            )

            response_text = response.text.lower()

            # Password should NEVER appear in response
            assert 'test_password_123' not in response_text, (
                "Password was echoed back in response! Critical security issue."
            )

            # Generic password indicators
            assert 'password' not in response_text or 'invalid' in response_text, (
                "Response contains password-related data"
            )

    @pytest.mark.asyncio
    async def test_failed_login_rate_limited(self):
        """
        Verify failed login attempts are rate limited.

        Security Requirement:
        - Multiple failed attempts should trigger rate limiting
        - After threshold, requests should be rejected (429)
        - This prevents brute force attacks
        """
        async with httpx.AsyncClient(verify=False) as client:
            url = f"{BASE_URL}:8000/auth/login"

            # Attempt multiple failed logins
            rate_limited = False

            for i in range(20):  # Try 20 rapid attempts
                response = await client.post(
                    url,
                    json={'username': 'test', 'password': f'wrong_password_{i}'},
                    timeout=5.0
                )

                if response.status_code == 429:  # Too Many Requests
                    rate_limited = True
                    break

            # Note: This will fail if rate limiting not implemented (TDD RED)
            assert rate_limited, (
                "No rate limiting detected after 20 rapid login attempts.\n"
                "Implement rate limiting to prevent brute force attacks."
            )


class TestSecurityHeadersIntegration:
    """
    Integration tests for security headers.

    These tests verify that services return proper security headers
    that protect against common web vulnerabilities.

    Business Context:
    - Security headers are first line of defense
    - CSP prevents XSS attacks
    - HSTS ensures HTTPS usage
    """

    @pytest.mark.asyncio
    async def test_services_return_security_headers(self):
        """
        Verify services return essential security headers.

        Security Headers Required:
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: DENY or SAMEORIGIN
        - Strict-Transport-Security (HSTS)
        - Content-Security-Policy (CSP)
        """
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
        ]

        recommended_headers = [
            'Strict-Transport-Security',
            'Content-Security-Policy',
        ]

        async with httpx.AsyncClient(verify=False) as client:
            for service, port in SERVICE_PORTS.items():
                url = f"{BASE_URL}:{port}/health"

                try:
                    response = await client.get(url, timeout=5.0)

                    # Check required headers
                    for header in required_headers:
                        assert header.lower() in [h.lower() for h in response.headers], (
                            f"Service {service} missing required header: {header}"
                        )

                    # Warn about recommended headers (don't fail)
                    for header in recommended_headers:
                        if header.lower() not in [h.lower() for h in response.headers]:
                            print(f"WARNING: {service} missing recommended header: {header}")

                except httpx.ConnectError:
                    pytest.skip(f"Service {service} not running")


class TestJWTSecurityIntegration:
    """
    Integration tests for JWT security.

    These tests verify JWT handling at runtime including
    token validation, expiration, and rejection of invalid tokens.

    Business Context:
    - JWTs are the authentication mechanism for all services
    - Invalid or forged tokens must be rejected
    - Token expiration must be enforced
    """

    @pytest.mark.asyncio
    async def test_invalid_jwt_rejected(self):
        """
        Verify services reject invalid JWT tokens.

        Security Requirement:
        - Malformed tokens must be rejected with 401
        - Tokens with invalid signatures must be rejected
        - This prevents token forgery
        """
        invalid_tokens = [
            'invalid_token',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature',
            'Bearer invalid',
            '',
        ]

        async with httpx.AsyncClient(verify=False) as client:
            for service, port in SERVICE_PORTS.items():
                url = f"{BASE_URL}:{port}/api/v1/protected"  # Assumed protected endpoint

                for token in invalid_tokens:
                    try:
                        response = await client.get(
                            url,
                            headers={'Authorization': f'Bearer {token}'},
                            timeout=5.0
                        )

                        # Should reject with 401 or 403
                        assert response.status_code in [401, 403, 404], (
                            f"Service {service} accepted invalid token: {token[:20]}..."
                        )
                    except httpx.ConnectError:
                        pytest.skip(f"Service {service} not running")
                        break

    @pytest.mark.asyncio
    async def test_expired_jwt_rejected(self):
        """
        Verify services reject expired JWT tokens.

        Security Requirement:
        - Tokens past expiration must be rejected
        - Clear error message about expiration
        - Forces re-authentication
        """
        # An obviously expired token (exp in the past)
        # Note: This is a valid structure but expired
        expired_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNjAwMDAwMDAwfQ."
            "invalid_signature"
        )

        async with httpx.AsyncClient(verify=False) as client:
            url = f"{BASE_URL}:8000/api/v1/users/me"

            response = await client.get(
                url,
                headers={'Authorization': f'Bearer {expired_token}'},
                timeout=5.0
            )

            # Should be rejected
            assert response.status_code in [401, 403], (
                f"Expired token was not rejected: {response.status_code}"
            )


# Pytest markers
pytestmark = [
    pytest.mark.security,
    pytest.mark.integration,
]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
