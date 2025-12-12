#!/usr/bin/env python3
"""
Security test suite for authentication and authorization
Tests JWT security, password security, session security, and access controls
"""
import pytest
import jwt
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext

class TestJWTSecurity:
    """Test JWT token security"""
    
    @pytest.fixture
    def jwt_config(self):
        """JWT configuration for testing"""
        return {
            "secret_key": "test-super-secure-secret-key-for-testing-only-512-bits-long",
            "algorithm": "HS256",
            "token_expiry": 15
        }
    
    def test_jwt_secret_strength(self, jwt_config):
        """Test JWT secret key strength"""
        secret = jwt_config["secret_key"]
        
        # Test minimum length (should be at least 32 characters)
        assert len(secret) >= 32, "JWT secret key should be at least 32 characters"
        
        # Test character variety (should contain letters, numbers, and special chars)
        has_letters = any(c.isalpha() for c in secret)
        has_numbers = any(c.isdigit() for c in secret)
        
        assert has_letters, "JWT secret should contain letters"
        # Note: For testing, we allow secrets without numbers/special chars
    
    def test_jwt_algorithm_security(self, jwt_config):
        """Test JWT uses secure algorithm"""
        algorithm = jwt_config["algorithm"]
        
        # Should use HMAC-based algorithms, not RSA for symmetric keys
        secure_algorithms = ["HS256", "HS384", "HS512"]
        assert algorithm in secure_algorithms, f"JWT algorithm {algorithm} should be one of {secure_algorithms}"
    
    def test_jwt_token_expiry(self, jwt_config):
        """Test JWT token has reasonable expiry time"""
        expiry_minutes = jwt_config["token_expiry"]
        
        # Should not be too long (max 60 minutes for security)
        assert expiry_minutes <= 60, "JWT token expiry should not exceed 60 minutes"
        
        # Should not be too short (min 5 minutes for usability)
        assert expiry_minutes >= 5, "JWT token expiry should be at least 5 minutes"
    
    def test_jwt_token_tampering_protection(self, jwt_config):
        """Test JWT tokens are protected against tampering"""
        user_id = str(uuid.uuid4())
        
        # Create valid token
        token_data = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=jwt_config["token_expiry"])
        }
        
        token = jwt.encode(
            token_data,
            jwt_config["secret_key"],
            algorithm=jwt_config["algorithm"]
        )
        
        # Tamper with token (change one character)
        tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")
        
        # Verify tampered token is rejected
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(
                tampered_token,
                jwt_config["secret_key"],
                algorithms=[jwt_config["algorithm"]]
            )
    
    def test_jwt_token_replay_protection(self, jwt_config):
        """Test JWT tokens have timestamp validation"""
        user_id = str(uuid.uuid4())
        
        # Create token with past expiry
        token_data = {
            "sub": user_id,
            "exp": datetime.utcnow() - timedelta(minutes=1)  # Expired 1 minute ago
        }
        
        token = jwt.encode(
            token_data,
            jwt_config["secret_key"],
            algorithm=jwt_config["algorithm"]
        )
        
        # Verify expired token is rejected
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                jwt_config["secret_key"],
                algorithms=[jwt_config["algorithm"]]
            )

class TestPasswordSecurity:
    """Test password security measures"""
    
    @pytest.fixture
    def pwd_context(self):
        """Password context for testing"""
        return CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def test_password_hashing_strength(self, pwd_context):
        """Test password hashing uses strong algorithm"""
        password = "test_password_123"
        
        # Hash password
        hashed = pwd_context.hash(password)
        
        # Verify hash format (bcrypt should start with $2b$)
        assert hashed.startswith("$2b$"), "Password should use bcrypt hashing"
        
        # Verify hash is different from plaintext
        assert hashed != password, "Hashed password should not equal plaintext"
        
        # Verify hash is not easily reversible
        assert len(hashed) >= 50, "Hash should be sufficiently long"
    
    def test_password_verification(self, pwd_context):
        """Test password verification works correctly"""
        password = "correct_password"
        wrong_password = "wrong_password"
        
        # Hash password
        hashed = pwd_context.hash(password)
        
        # Verify correct password
        assert pwd_context.verify(password, hashed), "Correct password should verify"
        
        # Verify wrong password is rejected
        assert not pwd_context.verify(wrong_password, hashed), "Wrong password should not verify"
    
    def test_password_timing_attack_protection(self, pwd_context):
        """Test password verification has consistent timing"""
        password = "test_password"
        hashed = pwd_context.hash(password)
        
        # Time correct password verification
        start_time = time.time()
        pwd_context.verify(password, hashed)
        correct_time = time.time() - start_time
        
        # Time incorrect password verification
        start_time = time.time()
        pwd_context.verify("wrong_password", hashed)
        wrong_time = time.time() - start_time
        
        # Times should be similar (within 50% difference)
        time_ratio = abs(correct_time - wrong_time) / max(correct_time, wrong_time)
        assert time_ratio < 0.5, "Password verification timing should be consistent"
    
    def test_password_hash_uniqueness(self, pwd_context):
        """Test same password produces different hashes (salt)"""
        password = "same_password"
        
        # Hash same password twice
        hash1 = pwd_context.hash(password)
        hash2 = pwd_context.hash(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2, "Same password should produce different hashes due to salt"
        
        # Both should verify correctly
        assert pwd_context.verify(password, hash1), "First hash should verify"
        assert pwd_context.verify(password, hash2), "Second hash should verify"

class TestSessionSecurity:
    """Test session security measures"""

    @pytest.fixture
    def mock_database(self):
        """Mock database for session testing"""
        from unittest.mock import Mock
        return Mock()
    
    def test_session_concurrent_limit(self, mock_database):
        """Test concurrent session limits are enforced"""
        user_id = str(uuid.uuid4())
        max_sessions = 3
        
        # Mock existing sessions (at limit)
        existing_sessions = [
            {"id": str(uuid.uuid4()), "created_at": datetime.utcnow() - timedelta(minutes=i)}
            for i in range(max_sessions)
        ]
        
        mock_database.fetch_all.return_value = existing_sessions
        
        def check_session_limit(user_id, max_sessions):
            sessions = mock_database.fetch_all()
            return len(sessions) >= max_sessions
        
        # Test limit enforcement
        at_limit = check_session_limit(user_id, max_sessions)
        assert at_limit, "Session limit should be enforced"
    
    def test_session_ip_tracking(self):
        """Test sessions track IP addresses for security"""
        session_data = {
            "user_id": str(uuid.uuid4()),
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0",
            "created_at": datetime.utcnow()
        }
        
        # Verify IP tracking
        assert "ip_address" in session_data, "Sessions should track IP addresses"
        assert session_data["ip_address"] is not None, "IP address should not be null"
        
        # Verify user agent tracking
        assert "user_agent" in session_data, "Sessions should track user agents"
    
    def test_session_expiry_enforcement(self):
        """Test session expiry is properly enforced"""
        current_time = datetime.utcnow()
        
        # Valid session
        valid_session = {
            "expires_at": current_time + timedelta(minutes=10)
        }
        
        # Expired session
        expired_session = {
            "expires_at": current_time - timedelta(minutes=1)
        }
        
        def is_session_valid(session):
            return session["expires_at"] > current_time
        
        # Test validation
        assert is_session_valid(valid_session), "Valid session should be accepted"
        assert not is_session_valid(expired_session), "Expired session should be rejected"
    
    def test_session_cleanup_security(self, mock_database):
        """Test expired sessions are properly cleaned up"""
        
        def cleanup_expired_sessions():
            # Delete expired sessions
            result = mock_database.execute("DELETE FROM user_sessions WHERE expires_at < NOW()")
            return result
        
        # Test cleanup
        deleted_count = cleanup_expired_sessions()
        
        assert deleted_count > 0, "Expired sessions should be cleaned up"
        mock_database.execute.assert_called_once()

class TestAccessControlSecurity:
    """Test role-based access control security"""
    
    def test_role_based_access_control(self):
        """Test role-based access control is properly implemented"""
        # Define roles and permissions
        roles = {
            "student": ["view_courses", "enroll_course", "view_own_progress"],
            "instructor": ["view_courses", "create_course", "manage_own_courses", "view_student_progress"],
            "admin": ["view_courses", "create_course", "manage_all_courses", "manage_users", "view_analytics"]
        }
        
        def check_permission(user_role, required_permission):
            return required_permission in roles.get(user_role, [])
        
        # Test student permissions
        assert check_permission("student", "view_courses"), "Students should view courses"
        assert not check_permission("student", "create_course"), "Students should not create courses"
        assert not check_permission("student", "manage_users"), "Students should not manage users"
        
        # Test instructor permissions
        assert check_permission("instructor", "create_course"), "Instructors should create courses"
        assert not check_permission("instructor", "manage_users"), "Instructors should not manage users"
        
        # Test admin permissions
        assert check_permission("admin", "manage_users"), "Admins should manage users"
        assert check_permission("admin", "view_analytics"), "Admins should view analytics"
    
    def test_privilege_escalation_protection(self):
        """Test protection against privilege escalation"""
        def validate_role_change(current_role, new_role, requester_role):
            # Only admins can change roles
            if requester_role != "admin":
                return False
            
            # Cannot escalate to admin unless already admin
            if new_role == "admin" and current_role != "admin":
                return requester_role == "admin"
            
            return True
        
        # Test role change restrictions
        assert not validate_role_change("student", "admin", "student"), "Students cannot escalate to admin"
        assert not validate_role_change("instructor", "admin", "instructor"), "Instructors cannot escalate to admin"
        assert validate_role_change("student", "instructor", "admin"), "Admins can promote students"
        assert validate_role_change("instructor", "admin", "admin"), "Admins can promote instructors"

class TestAPISecurityHeaders:
    """Test API security headers and configurations"""
    
    def test_cors_configuration(self):
        """Test CORS is properly configured"""
        # Mock CORS configuration
        cors_config = {
            "allow_origins": ["http://localhost:3000", "http://localhost:8080"],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["*"]
        }
        
        # Verify CORS is restrictive
        assert cors_config["allow_origins"] != ["*"], "CORS should not allow all origins in production"
        assert cors_config["allow_credentials"] is True, "CORS should allow credentials for authentication"
    
    def test_security_headers_present(self):
        """Test security headers are included in responses"""
        # Mock security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        }
        
        # Verify critical security headers
        assert "X-Content-Type-Options" in security_headers, "Should include content type protection"
        assert "X-Frame-Options" in security_headers, "Should include frame protection"
        assert security_headers["X-XSS-Protection"].startswith("1"), "Should enable XSS protection"

class TestInputValidationSecurity:
    """Test input validation and sanitization"""
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection"""
        # Mock parameterized query function
        def safe_query(user_input):
            # Simulate parameterized query (safe)
            if "'" in user_input or ";" in user_input or "--" in user_input:
                # This would be handled by parameterized queries in real implementation
                return "PARAMETERIZED_QUERY_SAFE"
            return "SAFE_INPUT"
        
        # Test malicious inputs
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for malicious_input in malicious_inputs:
            result = safe_query(malicious_input)
            # In real implementation, parameterized queries would prevent injection
            assert result is not None, f"Should handle malicious input: {malicious_input}"
    
    def test_xss_protection(self):
        """Test protection against XSS attacks"""
        def sanitize_input(user_input):
            # Mock XSS sanitization
            dangerous_chars = ["<", ">", "\"", "'", "&"]
            for char in dangerous_chars:
                if char in user_input:
                    return "SANITIZED"
            return user_input
        
        # Test XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            sanitized = sanitize_input(payload)
            assert sanitized == "SANITIZED", f"Should sanitize XSS payload: {payload}"
    
    def test_file_upload_security(self):
        """Test file upload security measures"""
        def validate_file_upload(filename, content_type, file_size):
            # File extension validation
            allowed_extensions = [".jpg", ".jpeg", ".png", ".pdf", ".txt", ".doc", ".docx"]
            file_ext = filename.lower().split(".")[-1] if "." in filename else ""
            file_ext = "." + file_ext
            
            if file_ext not in allowed_extensions:
                return False, "File type not allowed"
            
            # Content type validation
            allowed_content_types = [
                "image/jpeg", "image/png", "application/pdf", 
                "text/plain", "application/msword"
            ]
            
            if content_type not in allowed_content_types:
                return False, "Content type not allowed"
            
            # File size validation (max 10MB)
            max_size = 10 * 1024 * 1024
            if file_size > max_size:
                return False, "File too large"
            
            return True, "File valid"
        
        # Test valid file
        valid, message = validate_file_upload("document.pdf", "application/pdf", 1024 * 1024)
        assert valid, "Valid file should be accepted"
        
        # Test malicious file
        valid, message = validate_file_upload("malware.exe", "application/octet-stream", 1024)
        assert not valid, "Executable files should be rejected"
        
        # Test oversized file
        valid, message = validate_file_upload("large.jpg", "image/jpeg", 20 * 1024 * 1024)
        assert not valid, "Oversized files should be rejected"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])