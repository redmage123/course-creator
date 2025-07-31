"""
Security Tests for RBAC System
Tests authentication, authorization, and security vulnerabilities
"""

import pytest
import uuid
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Add test fixtures path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../fixtures'))

from rbac_fixtures import (
    rbac_test_data,
    RBACTestUtils
)


class TestRBACSecurity:
    """Security test cases for RBAC system"""
    
    @pytest.fixture
    def mock_security_context(self):
        """Create mock security context for testing."""
        context = Mock()
        context.current_user = None
        context.current_organization = None
        context.permissions = []
        context.is_authenticated = False
        context.session_token = None
        
        def authenticate(token):
            try:
                payload = jwt.decode(token, "test_secret", algorithms=["HS256"])
                context.current_user = {
                    "id": payload["user_id"],
                    "email": payload["email"],
                    "role": payload.get("role", "student"),
                    "organization_id": payload.get("organization_id"),
                    "is_site_admin": payload.get("is_site_admin", False),
                    "permissions": payload.get("permissions", [])
                }
                context.is_authenticated = True
                context.session_token = token
                return True
            except jwt.InvalidTokenError:
                context.is_authenticated = False
                return False
        
        context.authenticate = authenticate
        return context
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_jwt_token_validation_valid_token(self, mock_security_context, rbac_test_data):
        """Test JWT token validation with valid token."""
        # Arrange
        user_data = rbac_test_data["users"]["org_admin"]
        token = RBACTestUtils.create_test_jwt_token(user_data)
        
        # Act
        is_valid = mock_security_context.authenticate(token)
        
        # Assert
        assert is_valid is True
        assert mock_security_context.is_authenticated is True
        assert mock_security_context.current_user["id"] == user_data["id"]
        assert mock_security_context.current_user["email"] == user_data["email"]
        assert mock_security_context.current_user["role"] == user_data["role"]
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_jwt_token_validation_invalid_token(self, mock_security_context):
        """Test JWT token validation with invalid token."""
        # Arrange
        invalid_token = "invalid.jwt.token"
        
        # Act
        is_valid = mock_security_context.authenticate(invalid_token)
        
        # Assert
        assert is_valid is False
        assert mock_security_context.is_authenticated is False
        assert mock_security_context.current_user is None
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_jwt_token_validation_expired_token(self, mock_security_context, rbac_test_data):
        """Test JWT token validation with expired token."""
        # Arrange
        user_data = rbac_test_data["users"]["org_admin"]
        expired_payload = {
            "user_id": user_data["id"],
            "email": user_data["email"], 
            "role": user_data["role"],
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, "test_secret", algorithm="HS256")
        
        # Act
        is_valid = mock_security_context.authenticate(expired_token)
        
        # Assert
        assert is_valid is False
        assert mock_security_context.is_authenticated is False
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_jwt_token_validation_tampered_token(self, mock_security_context, rbac_test_data):
        """Test JWT token validation with tampered token."""
        # Arrange
        user_data = rbac_test_data["users"]["student"]
        valid_token = RBACTestUtils.create_test_jwt_token(user_data)
        
        # Tamper with the token
        tampered_token = valid_token[:-5] + "12345"
        
        # Act
        is_valid = mock_security_context.authenticate(tampered_token)
        
        # Assert
        assert is_valid is False
        assert mock_security_context.is_authenticated is False
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_role_based_access_control_site_admin(self, mock_security_context, rbac_test_data):
        """Test role-based access control for site admin."""
        # Arrange
        site_admin_data = rbac_test_data["users"]["site_admin"]
        token = RBACTestUtils.create_test_jwt_token(site_admin_data)
        mock_security_context.authenticate(token)
        
        # Mock permission check function
        def has_permission(permission):
            user = mock_security_context.current_user
            if user and user.get("is_site_admin"):
                return True  # Site admin has all permissions
            return False
        
        # Act & Assert
        assert has_permission("delete_organizations") is True
        assert has_permission("manage_platform") is True
        assert has_permission("view_audit_logs") is True
        assert has_permission("manage_integrations") is True
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_role_based_access_control_org_admin(self, mock_security_context, rbac_test_data):
        """Test role-based access control for organization admin."""
        # Arrange
        org_admin_data = rbac_test_data["users"]["org_admin"]
        token = RBACTestUtils.create_test_jwt_token(org_admin_data)
        mock_security_context.authenticate(token)
        
        # Mock permission check function
        def has_permission(permission):
            user = mock_security_context.current_user
            if user and user.get("role") == "organization_admin":
                org_admin_permissions = [
                    "manage_organization",
                    "manage_members",
                    "create_tracks",
                    "manage_meeting_rooms",
                    "view_analytics"
                ]
                return permission in org_admin_permissions
            return False
        
        # Act & Assert - Allowed permissions
        assert has_permission("manage_members") is True
        assert has_permission("create_tracks") is True
        assert has_permission("manage_meeting_rooms") is True
        
        # Act & Assert - Denied permissions
        assert has_permission("delete_organizations") is False
        assert has_permission("manage_platform") is False
        assert has_permission("manage_integrations") is False
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_role_based_access_control_instructor(self, mock_security_context, rbac_test_data):
        """Test role-based access control for instructor."""
        # Arrange
        instructor_data = rbac_test_data["users"]["instructor"]
        token = RBACTestUtils.create_test_jwt_token(instructor_data)
        mock_security_context.authenticate(token)
        
        # Mock permission check function
        def has_permission(permission):
            user = mock_security_context.current_user
            if user and user.get("role") == "instructor":
                instructor_permissions = [
                    "create_courses",
                    "manage_students",
                    "access_analytics",
                    "create_meeting_rooms"
                ]
                return permission in instructor_permissions
            return False
        
        # Act & Assert - Allowed permissions
        assert has_permission("create_courses") is True
        assert has_permission("manage_students") is True
        assert has_permission("access_analytics") is True
        
        # Act & Assert - Denied permissions
        assert has_permission("manage_members") is False
        assert has_permission("delete_organizations") is False
        assert has_permission("manage_platform") is False
    
    @pytest.mark.security
    @pytest.mark.auth
    def test_role_based_access_control_student(self, mock_security_context, rbac_test_data):
        """Test role-based access control for student."""
        # Arrange
        student_data = rbac_test_data["users"]["student"]
        token = RBACTestUtils.create_test_jwt_token(student_data)
        mock_security_context.authenticate(token)
        
        # Mock permission check function
        def has_permission(permission):
            user = mock_security_context.current_user
            if user and user.get("role") == "student":
                student_permissions = [
                    "view_courses",
                    "submit_assignments",
                    "access_labs",
                    "take_quizzes"
                ]
                return permission in student_permissions
            return False
        
        # Act & Assert - Allowed permissions
        assert has_permission("view_courses") is True
        assert has_permission("submit_assignments") is True
        assert has_permission("access_labs") is True
        assert has_permission("take_quizzes") is True
        
        # Act & Assert - Denied permissions
        assert has_permission("create_courses") is False
        assert has_permission("manage_students") is False
        assert has_permission("manage_members") is False
        assert has_permission("delete_organizations") is False
    
    @pytest.mark.security
    def test_organization_boundary_enforcement(self, mock_security_context, rbac_test_data):
        """Test that users can only access resources within their organization."""
        # Arrange
        user_org_id = rbac_test_data["organization"]["id"]
        other_org_id = str(uuid.uuid4())
        
        org_admin_data = rbac_test_data["users"]["org_admin"]
        token = RBACTestUtils.create_test_jwt_token(org_admin_data)
        mock_security_context.authenticate(token)
        
        # Mock organization boundary check
        def can_access_organization(requested_org_id):
            user = mock_security_context.current_user
            if not user:
                return False
            
            # Site admins can access any organization
            if user.get("is_site_admin"):
                return True
            
            # Other users can only access their own organization
            return user.get("organization_id") == requested_org_id
        
        # Act & Assert
        assert can_access_organization(user_org_id) is True  # Own organization
        assert can_access_organization(other_org_id) is False  # Other organization
        assert can_access_organization(None) is False  # No organization
    
    @pytest.mark.security
    def test_privilege_escalation_prevention(self, mock_security_context, rbac_test_data):
        """Test prevention of privilege escalation attacks."""
        # Arrange
        instructor_data = rbac_test_data["users"]["instructor"]
        token = RBACTestUtils.create_test_jwt_token(instructor_data)
        mock_security_context.authenticate(token)
        
        # Mock role modification attempt
        def attempt_role_modification(target_user_id, new_role):
            current_user = mock_security_context.current_user
            if not current_user:
                return False, "Not authenticated"
            
            # Only organization admins can modify roles
            if current_user.get("role") != "organization_admin":
                return False, "Insufficient permissions"
            
            # Cannot elevate to site admin
            if new_role == "site_admin":
                return False, "Cannot grant site admin privileges"
            
            return True, "Role modified successfully"
        
        # Act & Assert - Instructor trying to modify roles
        success, message = attempt_role_modification(str(uuid.uuid4()), "organization_admin")
        assert success is False
        assert "Insufficient permissions" in message
        
        # Mock organization admin
        org_admin_data = rbac_test_data["users"]["org_admin"] 
        token = RBACTestUtils.create_test_jwt_token(org_admin_data)
        mock_security_context.authenticate(token)
        
        # Org admin trying to grant site admin
        success, message = attempt_role_modification(str(uuid.uuid4()), "site_admin")
        assert success is False
        assert "Cannot grant site admin privileges" in message
        
        # Org admin granting valid role
        success, message = attempt_role_modification(str(uuid.uuid4()), "instructor")
        assert success is True
    
    @pytest.mark.security
    def test_session_management_security(self, mock_security_context):
        """Test session management security features."""
        # Mock session manager
        session_manager = Mock()
        session_manager.active_sessions = {}
        session_manager.session_timeout = timedelta(hours=8)
        session_manager.max_concurrent_sessions = 3
        
        def create_session(user_id, token):
            session_id = str(uuid.uuid4())
            session = {
                "id": session_id,
                "user_id": user_id,
                "token": token,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            }
            
            # Check concurrent session limit
            user_sessions = [s for s in session_manager.active_sessions.values() 
                           if s["user_id"] == user_id]
            if len(user_sessions) >= session_manager.max_concurrent_sessions:
                # Remove oldest session
                oldest_session = min(user_sessions, key=lambda s: s["created_at"])
                del session_manager.active_sessions[oldest_session["id"]]
            
            session_manager.active_sessions[session_id] = session
            return session_id
        
        def validate_session(session_id):
            session = session_manager.active_sessions.get(session_id)
            if not session:
                return False, "Session not found"
            
            # Check session timeout
            if datetime.utcnow() - session["last_activity"] > session_manager.session_timeout:
                del session_manager.active_sessions[session_id]
                return False, "Session expired"
            
            # Update last activity
            session["last_activity"] = datetime.utcnow()
            return True, "Session valid"
        
        session_manager.create_session = create_session
        session_manager.validate_session = validate_session
        
        # Test session creation
        user_id = str(uuid.uuid4())
        token = "test_token"
        session_id = session_manager.create_session(user_id, token)
        
        assert session_id in session_manager.active_sessions
        
        # Test session validation
        valid, message = session_manager.validate_session(session_id)
        assert valid is True
        assert message == "Session valid"
        
        # Test session timeout
        session = session_manager.active_sessions[session_id]
        session["last_activity"] = datetime.utcnow() - timedelta(hours=9)  # Expired
        
        valid, message = session_manager.validate_session(session_id)
        assert valid is False
        assert message == "Session expired"
        assert session_id not in session_manager.active_sessions
    
    @pytest.mark.security
    def test_input_validation_sql_injection_prevention(self):
        """Test input validation to prevent SQL injection attacks."""
        # Mock input validator
        def validate_organization_name(name):
            if not name:
                raise ValueError("Organization name is required")
            
            # Check for SQL injection patterns
            sql_patterns = ["'", "\"", ";", "--", "/*", "*/", "xp_", "sp_", "DROP", "SELECT", "INSERT", "UPDATE", "DELETE"]
            name_upper = name.upper()
            
            for pattern in sql_patterns:
                if pattern.upper() in name_upper:
                    raise ValueError("Invalid characters in organization name")
            
            if len(name) > 100:
                raise ValueError("Organization name too long")
            
            return True
        
        # Test valid input
        assert validate_organization_name("Valid Organization Name") is True
        
        # Test SQL injection attempts
        injection_attempts = [
            "Test'; DROP TABLE organizations; --",
            "Test\" OR 1=1; --",
            "Test/*comment*/",
            "Test UNION SELECT * FROM users",
            "'; DELETE FROM organizations WHERE id = 1; --"
        ]
        
        for attempt in injection_attempts:
            with pytest.raises(ValueError, match="Invalid characters"):
                validate_organization_name(attempt)
    
    @pytest.mark.security
    def test_input_validation_xss_prevention(self):
        """Test input validation to prevent XSS attacks."""
        # Mock XSS validator
        def validate_description(description):
            if not description:
                return True  # Optional field
            
            # Check for XSS patterns
            xss_patterns = ["<script", "</script>", "javascript:", "onload=", "onerror=", "onclick=", "alert(", "eval("]
            description_lower = description.lower()
            
            for pattern in xss_patterns:
                if pattern in description_lower:
                    raise ValueError("Invalid content in description")
            
            if len(description) > 1000:
                raise ValueError("Description too long")
            
            return True
        
        # Test valid input
        assert validate_description("This is a valid description.") is True
        assert validate_description("") is True  # Empty is allowed
        
        # Test XSS attempts
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<div onclick=alert('XSS')>Click me</div>",
            "eval('malicious code')"
        ]
        
        for attempt in xss_attempts:
            with pytest.raises(ValueError, match="Invalid content"):
                validate_description(attempt)
    
    @pytest.mark.security
    def test_rate_limiting_protection(self):
        """Test rate limiting protection against brute force attacks."""
        # Mock rate limiter
        rate_limiter = Mock()
        rate_limiter.requests = {}
        rate_limiter.max_requests = 5
        rate_limiter.time_window = timedelta(minutes=1)
        
        def check_rate_limit(ip_address, endpoint):
            now = datetime.utcnow()
            key = f"{ip_address}:{endpoint}"
            
            if key not in rate_limiter.requests:
                rate_limiter.requests[key] = []
            
            # Clean old requests
            rate_limiter.requests[key] = [
                req_time for req_time in rate_limiter.requests[key]
                if now - req_time <= rate_limiter.time_window
            ]
            
            # Check limit
            if len(rate_limiter.requests[key]) >= rate_limiter.max_requests:
                return False, "Rate limit exceeded"
            
            # Add current request
            rate_limiter.requests[key].append(now)
            return True, "Request allowed"
        
        rate_limiter.check_rate_limit = check_rate_limit
        
        # Test normal usage
        ip = "192.168.1.100"
        endpoint = "/api/v1/auth/login"
        
        for i in range(5):
            allowed, message = rate_limiter.check_rate_limit(ip, endpoint)
            assert allowed is True
            assert message == "Request allowed"
        
        # Test rate limit exceeded
        allowed, message = rate_limiter.check_rate_limit(ip, endpoint)
        assert allowed is False
        assert message == "Rate limit exceeded"
    
    @pytest.mark.security
    def test_audit_logging_security_events(self):
        """Test audit logging of security-related events."""
        # Mock audit logger
        audit_logger = Mock()
        audit_logger.logs = []
        
        def log_security_event(event_type, user_id, details, ip_address=None):
            log_entry = {
                "id": str(uuid.uuid4()),
                "event_type": event_type,
                "user_id": user_id,
                "details": details,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow(),
                "severity": "HIGH" if event_type in ["failed_login", "privilege_escalation", "unauthorized_access"] else "MEDIUM"
            }
            audit_logger.logs.append(log_entry)
            return log_entry["id"]
        
        audit_logger.log_security_event = log_security_event
        
        # Test logging various security events
        user_id = str(uuid.uuid4())
        ip_address = "192.168.1.100"
        
        # Login failure
        log_id = audit_logger.log_security_event(
            "failed_login",
            user_id,
            {"reason": "invalid_password", "attempt_count": 3},
            ip_address
        )
        
        # Privilege escalation attempt
        audit_logger.log_security_event(
            "privilege_escalation",
            user_id,
            {"attempted_role": "site_admin", "current_role": "instructor"},
            ip_address
        )
        
        # Unauthorized access attempt
        audit_logger.log_security_event(
            "unauthorized_access",
            user_id,
            {"resource": "/api/v1/site-admin/organizations", "required_role": "site_admin"},
            ip_address
        )
        
        # Verify logs
        assert len(audit_logger.logs) == 3
        
        failed_login_log = next((log for log in audit_logger.logs if log["event_type"] == "failed_login"), None)
        assert failed_login_log is not None
        assert failed_login_log["severity"] == "HIGH"
        assert failed_login_log["details"]["attempt_count"] == 3
        
        privilege_escalation_log = next((log for log in audit_logger.logs if log["event_type"] == "privilege_escalation"), None)
        assert privilege_escalation_log is not None
        assert privilege_escalation_log["severity"] == "HIGH"
        
        unauthorized_access_log = next((log for log in audit_logger.logs if log["event_type"] == "unauthorized_access"), None)
        assert unauthorized_access_log is not None
        assert unauthorized_access_log["severity"] == "HIGH"
    
    @pytest.mark.security
    def test_password_security_requirements(self):
        """Test password security requirements and validation."""
        # Mock password validator
        def validate_password(password):
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters long")
            
            if len(password) > 128:
                raise ValueError("Password must be no more than 128 characters long")
            
            # Check for required character types
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
            
            if not has_upper:
                raise ValueError("Password must contain at least one uppercase letter")
            if not has_lower:
                raise ValueError("Password must contain at least one lowercase letter")
            if not has_digit:
                raise ValueError("Password must contain at least one digit")
            if not has_special:
                raise ValueError("Password must contain at least one special character")
            
            # Check for common weak passwords
            weak_passwords = ["password123", "admin123", "123456789", "qwerty123", "password123!"]
            if password.lower() in [p.lower() for p in weak_passwords]:
                raise ValueError("Password is too common")
            
            return True
        
        # Test valid passwords
        valid_passwords = [
            "SecurePass123!",
            "MyStr0ng@Password",
            "Complex#Pass123"
        ]
        
        for password in valid_passwords:
            assert validate_password(password) is True
        
        # Test invalid passwords
        invalid_passwords = [
            ("short", "Password must be at least 8 characters long"),
            ("nouppercase123!", "Password must contain at least one uppercase letter"),
            ("NOLOWERCASE123!", "Password must contain at least one lowercase letter"),
            ("NoDigitsHere!", "Password must contain at least one digit"),
            ("NoSpecialChars123", "Password must contain at least one special character"),
            ("Password123!", "Password is too common")
        ]
        
        for password, expected_error in invalid_passwords:
            with pytest.raises(ValueError, match=expected_error):
                validate_password(password)
    
    @pytest.mark.security
    def test_secure_api_communication(self):
        """Test secure API communication requirements."""
        # Mock API security validator
        def validate_api_request(request):
            # Check HTTPS requirement
            if not request.get("is_secure", False):
                raise ValueError("HTTPS required")
            
            # Check authentication header
            auth_header = request.get("headers", {}).get("Authorization")
            if not auth_header:
                raise ValueError("Authentication required")
            
            if not auth_header.startswith("Bearer "):
                raise ValueError("Invalid authentication format")
            
            # Check content type for POST/PUT requests
            method = request.get("method", "GET")
            if method in ["POST", "PUT", "PATCH"]:
                content_type = request.get("headers", {}).get("Content-Type")
                if content_type != "application/json":
                    raise ValueError("JSON content type required")
            
            # Check for CSRF token in sensitive operations
            if method in ["POST", "PUT", "DELETE"]:
                csrf_token = request.get("headers", {}).get("X-CSRF-Token")
                if not csrf_token:
                    raise ValueError("CSRF token required")
            
            return True
        
        # Test valid API request
        valid_request = {
            "method": "POST",
            "is_secure": True,
            "headers": {
                "Authorization": "Bearer valid_jwt_token",
                "Content-Type": "application/json",
                "X-CSRF-Token": "csrf_token_123"
            }
        }
        
        assert validate_api_request(valid_request) is True
        
        # Test invalid API requests
        invalid_requests = [
            ({
                "method": "POST",
                "is_secure": False,
                "headers": {"Authorization": "Bearer token"}
            }, "HTTPS required"),
            ({
                "method": "POST",
                "is_secure": True,
                "headers": {}
            }, "Authentication required"),
            ({
                "method": "POST",
                "is_secure": True,
                "headers": {"Authorization": "Basic credentials"}
            }, "Invalid authentication format"),
            ({
                "method": "POST",
                "is_secure": True,
                "headers": {
                    "Authorization": "Bearer token",
                    "Content-Type": "text/plain"
                }
            }, "JSON content type required"),
            ({
                "method": "DELETE",
                "is_secure": True,
                "headers": {
                    "Authorization": "Bearer token",
                    "Content-Type": "application/json"
                }
            }, "CSRF token required")
        ]
        
        for request, expected_error in invalid_requests:
            with pytest.raises(ValueError, match=expected_error):
                validate_api_request(request)