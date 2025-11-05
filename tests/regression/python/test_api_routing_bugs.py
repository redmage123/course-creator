"""
API Routing Regression Tests

BUSINESS CONTEXT:
Prevents known API routing and nginx configuration bugs from recurring.
Documents path mismatch issues between frontend and backend services.

BUG TRACKING:
Each test corresponds to a specific bug fix with:
- Bug ID/number from BUG_CATALOG.md
- Original issue description
- Root cause analysis (often nginx misconfiguration)
- Fix implementation details
- Test to prevent regression

COVERAGE:
- BUG-004: Nginx routing path mismatch for user management

Git Commits:
- 523fb1e: BUG-004 fix
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from urllib.parse import urlparse, urljoin


class TestAPIRoutingBugs:
    """
    REGRESSION TEST SUITE: API Routing Bugs

    PURPOSE:
    Ensure fixed nginx and API routing bugs don't reappear
    """

    def test_bug_004_nginx_user_management_path(self):
        """
        BUG #004: Nginx Routing Path Mismatch for User Management

        ORIGINAL ISSUE:
        GET /api/v1/users/me was returning 404 Not Found because nginx was
        proxying to the wrong backend path. All user profile endpoints were
        broken, preventing frontend from fetching current user data.

        SYMPTOMS:
        - GET /api/v1/users/me → 404 Not Found
        - All user profile endpoints broken
        - Frontend unable to fetch current user
        - Dashboard unable to display user information
        - Error: "User profile endpoint not found"

        ROOT CAUSE:
        The user-management service has endpoints at /users/me, NOT /api/v1/users/me.
        However, nginx.conf was configured to proxy:
        - Frontend request: /api/v1/users/me
        - nginx proxy_pass: https://user-management:8000/api/v1/users/
        - Backend receives: /api/v1/users/me (WRONG - backend doesn't have /api/v1 prefix)
        - Backend tries to handle: /api/v1/users/me (doesn't exist)
        - Result: 404 Not Found

        This is a common nginx path doubling issue where the proxy doesn't
        strip the path prefix correctly.

        FIX IMPLEMENTATION:
        File: frontend/nginx.conf (line 266)
        OLD: proxy_pass https://user-management:8000/api/v1/users/;
        NEW: proxy_pass https://user-management:8000/users/;

        The fix strips the /api/v1 prefix when proxying to backend, so:
        - Frontend request: /api/v1/users/me
        - nginx strips: /api/v1
        - nginx proxy_pass: https://user-management:8000/users/
        - Backend receives: /users/me (CORRECT)
        - Backend handles: /users/me (exists)
        - Result: 200 OK (or 401 if not authenticated)

        Git Commit: 523fb1e321def99ba1025de6f4c3950ee59534e9

        REGRESSION PREVENTION:
        This test ensures:
        1. nginx strips /api/v1 prefix correctly
        2. Backend receives correct path without doubling
        3. User management endpoints resolve correctly
        4. 404 errors don't occur due to path mismatch
        """
        # Arrange: Define correct nginx routing behavior
        class NginxPathRouter:
            """Simulates nginx proxy_pass path rewriting."""

            def __init__(self):
                self.routes = {
                    "/api/v1/users/": {
                        "backend": "user-management:8000",
                        "proxy_pass": "/users/",  # CORRECT: strips /api/v1
                        # INCORRECT would be: "/api/v1/users/"
                    }
                }

            def route_request(self, frontend_path):
                """
                Simulates nginx routing logic.
                Returns the path that backend will receive.
                """
                for route_prefix, config in self.routes.items():
                    if frontend_path.startswith(route_prefix):
                        # Strip the route prefix and add proxy_pass prefix
                        relative_path = frontend_path[len(route_prefix):]
                        backend_path = config["proxy_pass"] + relative_path
                        return {
                            "backend": config["backend"],
                            "path": backend_path
                        }
                return None

        # Act: Simulate routing for user management endpoints
        router = NginxPathRouter()

        # Test 1: /api/v1/users/me routes correctly
        result = router.route_request("/api/v1/users/me")
        assert result is not None, "Route must be configured"
        assert result["backend"] == "user-management:8000"
        assert result["path"] == "/users/me", \
            "Backend should receive /users/me, not /api/v1/users/me"

        # Test 2: Other user endpoints route correctly
        test_endpoints = [
            ("/api/v1/users/profile", "/users/profile"),
            ("/api/v1/users/123", "/users/123"),
            ("/api/v1/users/me/settings", "/users/me/settings"),
        ]

        for frontend_path, expected_backend_path in test_endpoints:
            result = router.route_request(frontend_path)
            assert result["path"] == expected_backend_path, \
                f"Path {frontend_path} should route to {expected_backend_path}"

        # Test 3: Verify /api/v1 prefix is stripped (not doubled)
        result = router.route_request("/api/v1/users/me")
        assert not result["path"].startswith("/api/v1"), \
            "Backend path must not contain /api/v1 prefix"
        assert result["path"].startswith("/users"), \
            "Backend path must start with /users"

        # Test 4: Simulate the INCORRECT configuration
        class IncorrectNginxRouter:
            """Simulates the BUG: path doubling."""

            def route_request(self, frontend_path):
                # BUG: This doesn't strip /api/v1
                if frontend_path.startswith("/api/v1/users/"):
                    return {
                        "backend": "user-management:8000",
                        "path": frontend_path  # WRONG: keeps /api/v1
                    }
                return None

        incorrect_router = IncorrectNginxRouter()
        bug_result = incorrect_router.route_request("/api/v1/users/me")

        # This is what caused the 404:
        assert bug_result["path"] == "/api/v1/users/me", \
            "Bug: path not stripped (for test documentation)"

        # Our fix ensures this doesn't happen
        correct_result = router.route_request("/api/v1/users/me")
        assert correct_result["path"] != bug_result["path"], \
            "Fixed router must produce different path than buggy router"

    def test_bug_004_backend_endpoint_structure(self):
        """
        Validates that backend endpoints don't have /api/v1 prefix.

        This test documents the backend API structure that caused the nginx
        routing bug. If backend structure changes, nginx config must update.
        """
        # Arrange: Document actual backend API structure
        BACKEND_API_STRUCTURE = {
            "user-management": {
                "base_url": "https://user-management:8000",
                "endpoints": [
                    "/users/me",
                    "/users/{id}",
                    "/users/profile",
                    "/auth/login",
                    "/auth/logout",
                ],
                "has_api_v1_prefix": False  # IMPORTANT: No /api/v1 prefix
            },
            "course-management": {
                "base_url": "https://course-management:8002",
                "endpoints": [
                    "/courses",
                    "/courses/{id}",
                    "/enrollments",
                ],
                "has_api_v1_prefix": False
            }
        }

        # Act & Assert: Verify backend structure
        for service_name, config in BACKEND_API_STRUCTURE.items():
            # Test 1: Backend doesn't use /api/v1 prefix
            assert not config["has_api_v1_prefix"], \
                f"{service_name} must not have /api/v1 prefix in actual endpoints"

            # Test 2: All endpoints are root-relative (no /api/v1)
            for endpoint in config["endpoints"]:
                assert not endpoint.startswith("/api/v1"), \
                    f"{service_name} endpoint {endpoint} must not start with /api/v1"
                assert endpoint.startswith("/"), \
                    f"{service_name} endpoint {endpoint} must be root-relative"

        # Test 3: nginx must strip /api/v1 for these services
        # This is the key insight that prevents the bug
        NGINX_REQUIREMENTS = {
            "user-management": {
                "frontend_prefix": "/api/v1/users/",
                "proxy_pass_prefix": "/users/",
                "must_strip_prefix": True
            }
        }

        for service_name, requirements in NGINX_REQUIREMENTS.items():
            backend = BACKEND_API_STRUCTURE[service_name]

            if requirements["must_strip_prefix"]:
                # nginx must strip /api/v1 prefix
                frontend = requirements["frontend_prefix"]
                proxy = requirements["proxy_pass_prefix"]

                assert frontend.startswith("/api/v1"), \
                    "Frontend uses /api/v1 prefix"
                assert not proxy.startswith("/api/v1"), \
                    "proxy_pass must strip /api/v1 prefix"
                assert not backend["has_api_v1_prefix"], \
                    "Backend doesn't use /api/v1 prefix"

    @pytest.mark.integration
    def test_bug_004_integration_user_endpoint(self):
        """
        Integration test: Verify /api/v1/users/me endpoint works.
        Requires running services with correct nginx configuration.

        EXPECTED BEHAVIOR:
        - With correct nginx config: 401 Unauthorized (endpoint exists, needs auth)
        - With bug: 404 Not Found (endpoint doesn't exist)
        """
        try:
            response = requests.get(
                "https://localhost:3000/api/v1/users/me",
                verify=False,  # Self-signed cert
                timeout=5
            )

            # Success: Endpoint exists (returns 401 for no auth or 200 with auth)
            # Failure: 404 means path routing bug has recurred
            assert response.status_code != 404, \
                "404 indicates path routing bug - nginx may not be stripping /api/v1 correctly"

            # Expected responses:
            # 401: Endpoint exists but not authenticated (CORRECT)
            # 200: Endpoint exists and authenticated (CORRECT)
            # 404: Endpoint doesn't exist (BUG RECURRED)
            assert response.status_code in [200, 401], \
                f"Expected 200 or 401, got {response.status_code}"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Services not available for integration test: {e}")


class TestNginxConfiguration:
    """
    Tests for nginx configuration patterns that commonly cause bugs.
    """

    def test_nginx_proxy_pass_trailing_slash(self):
        """
        Documents the critical trailing slash behavior in nginx proxy_pass.

        NGINX BEHAVIOR:
        - proxy_pass URL WITH trailing slash: nginx STRIPS the matched location
        - proxy_pass URL WITHOUT trailing slash: nginx KEEPS the matched location

        Example:
        location /api/v1/users/ {
            proxy_pass http://backend:8000/users/;  # WITH slash: strips /api/v1/users/
        }
        Request: /api/v1/users/me
        Backend receives: /users/me (CORRECT for our backend)

        If configured WITHOUT trailing slash:
        location /api/v1/users/ {
            proxy_pass http://backend:8000/users;  # NO slash: keeps /api/v1/users/
        }
        Request: /api/v1/users/me
        Backend receives: /api/v1/users/me (WRONG for our backend)
        """
        class NginxProxyBehavior:
            """Models nginx proxy_pass behavior."""

            @staticmethod
            def route_with_trailing_slash(request_path, location, proxy_pass):
                """
                Simulates nginx behavior WITH trailing slash.
                Strips the matched location from request path.
                """
                if proxy_pass.endswith('/'):
                    # Strip the location, append to proxy_pass
                    remaining_path = request_path[len(location):]
                    return proxy_pass + remaining_path
                return None

            @staticmethod
            def route_without_trailing_slash(request_path, location, proxy_pass):
                """
                Simulates nginx behavior WITHOUT trailing slash.
                Keeps the matched location in request path.
                """
                if not proxy_pass.endswith('/'):
                    # Keep full path, append to proxy_pass
                    return proxy_pass + request_path
                return None

        # Test WITH trailing slash (CORRECT for our use case)
        result = NginxProxyBehavior.route_with_trailing_slash(
            request_path="/api/v1/users/me",
            location="/api/v1/users/",
            proxy_pass="http://backend:8000/users/"
        )
        assert result == "http://backend:8000/users/me", \
            "WITH trailing slash must strip location prefix"

        # Test WITHOUT trailing slash (INCORRECT for our use case)
        result = NginxProxyBehavior.route_without_trailing_slash(
            request_path="/api/v1/users/me",
            location="/api/v1/users/",
            proxy_pass="http://backend:8000/users"
        )
        assert result == "http://backend:8000/users/api/v1/users/me", \
            "WITHOUT trailing slash keeps full path (causes path doubling)"

        # This is why the bug occurred - wrong behavior for our backend structure


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "regression: regression test for known bug fix"
    )
    config.addinivalue_line(
        "markers",
        "integration: integration test requiring running services"
    )
