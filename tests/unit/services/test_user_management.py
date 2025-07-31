"""
Unit tests for User Management Service

Tests all components of the user management service including:
- User models validation
- Authentication utilities
- Password management
- Session management
- User repositories
- User services
- API routes
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException
from passlib.context import CryptContext
import jwt
import uuid
import os

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/user-management'))

from models.user import User, UserCreate, UserUpdate, UserResponse, UserRole, UserSession
from models.common import BaseModel, ErrorResponse, SuccessResponse
from auth.password_manager import PasswordManager
from auth.jwt_manager import JWTManager
from auth.session_manager import SessionManager
from repositories.user_repository import UserRepository
from services.user_service import UserService


class TestUserModels:
    """Test user data models."""
    
    def test_user_base_model_validation(self):
        """Test basic user model validation."""
        # Valid user data
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        user_create = UserCreate(**user_data, password="password123")
        assert user_create.username == "testuser"
        assert user_create.email == "test@example.com"
        assert user_create.full_name == "Test User"
        assert user_create.password == "password123"
        assert user_create.role == UserRole.STUDENT  # Default role
    
    def test_user_email_validation(self):
        """Test email validation."""
        # Invalid email should raise ValidationError
        with pytest.raises(ValueError):
            UserCreate(
                username="testuser",
                email="invalid-email",
                full_name="Test User",
                password="password123"
            )
    
    def test_user_role_validation(self):
        """Test user role validation."""
        # Valid roles
        for role in [UserRole.STUDENT, UserRole.INSTRUCTOR, UserRole.ADMIN]:
            user = UserCreate(
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                password="password123",
                role=role
            )
            assert user.role == role
    
    def test_user_password_validation(self):
        """Test password validation."""
        # Password too short
        with pytest.raises(ValueError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                password="123"
            )
    
    def test_user_session_model(self):
        """Test user session model."""
        session_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "token": "test-token",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        session = UserSession(**session_data)
        assert session.user_id == session_data["user_id"]
        assert session.token == session_data["token"]
        assert not session.is_expired()
    
    def test_user_session_expiration(self):
        """Test session expiration logic."""
        # Expired session
        session = UserSession(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            token="test-token",
            expires_at=datetime.utcnow() - timedelta(hours=1),
            created_at=datetime.utcnow() - timedelta(hours=2),
            last_activity=datetime.utcnow() - timedelta(hours=1)
        )
        
        assert session.is_expired()


class TestPasswordManager:
    """Test password management utilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.password_manager = PasswordManager()
    
    def test_password_hashing(self):
        """Test password hashing."""
        password = "test_password123"
        hashed = self.password_manager.hash_password(password)
        
        assert hashed != password
        assert self.password_manager.verify_password(password, hashed)
    
    def test_password_verification(self):
        """Test password verification."""
        password = "test_password123"
        wrong_password = "wrong_password"
        hashed = self.password_manager.hash_password(password)
        
        assert self.password_manager.verify_password(password, hashed)
        assert not self.password_manager.verify_password(wrong_password, hashed)
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Weak passwords
        weak_passwords = ["123", "password", "abc", "11111111"]
        for weak_password in weak_passwords:
            assert not self.password_manager.is_strong_password(weak_password)
        
        # Strong passwords
        strong_passwords = ["StrongP@ssw0rd", "MySecure123!", "Complex$Pass1"]
        for strong_password in strong_passwords:
            assert self.password_manager.is_strong_password(strong_password)
    
    def test_password_policy_enforcement(self):
        """Test password policy enforcement."""
        # Test minimum length
        assert not self.password_manager.validate_password_policy("abc")
        
        # Test complexity requirements
        assert not self.password_manager.validate_password_policy("password")
        assert not self.password_manager.validate_password_policy("PASSWORD")
        assert not self.password_manager.validate_password_policy("12345678")
        
        # Valid password
        assert self.password_manager.validate_password_policy("ValidPass123!")


class TestJWTManager:
    """Test JWT token management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.jwt_manager = JWTManager()
    
    def test_token_creation(self):
        """Test JWT token creation."""
        user_id = str(uuid.uuid4())
        token = self.jwt_manager.create_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_validation(self):
        """Test JWT token validation."""
        user_id = str(uuid.uuid4())
        token = self.jwt_manager.create_token(user_id)
        
        payload = self.jwt_manager.validate_token(token)
        assert payload["user_id"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    def test_token_expiration(self):
        """Test token expiration."""
        user_id = str(uuid.uuid4())
        
        # Create token with short expiration
        token = self.jwt_manager.create_token(
            user_id, 
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        # Should raise exception for expired token
        with pytest.raises(jwt.ExpiredSignatureError):
            self.jwt_manager.validate_token(token)
    
    def test_invalid_token(self):
        """Test invalid token handling."""
        # Invalid token format
        with pytest.raises(jwt.InvalidTokenError):
            self.jwt_manager.validate_token("invalid.token.format")
        
        # Tampered token
        user_id = str(uuid.uuid4())
        token = self.jwt_manager.create_token(user_id)
        tampered_token = token[:-5] + "12345"  # Change last 5 characters
        
        with pytest.raises(jwt.InvalidSignatureError):
            self.jwt_manager.validate_token(tampered_token)
    
    def test_token_refresh(self):
        """Test token refresh functionality."""
        user_id = str(uuid.uuid4())
        original_token = self.jwt_manager.create_token(user_id)
        
        # Refresh token
        new_token = self.jwt_manager.refresh_token(original_token)
        
        # Both tokens should be valid and contain same user_id
        original_payload = self.jwt_manager.validate_token(original_token)
        new_payload = self.jwt_manager.validate_token(new_token)
        
        assert original_payload["user_id"] == new_payload["user_id"]
        assert new_payload["iat"] > original_payload["iat"]


class TestSessionManager:
    """Test session management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_pool = AsyncMock()
        self.session_manager = SessionManager(self.mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test session creation."""
        user_id = str(uuid.uuid4())
        token = "test-token"
        
        # Mock database response
        mock_row = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "token": token,
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "ip_address": "127.0.0.1",
            "user_agent": "Test Agent"
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        session = await self.session_manager.create_session(user_id, token)
        
        assert session is not None
        assert session.user_id == user_id
        assert session.token == token
    
    @pytest.mark.asyncio
    async def test_validate_session(self):
        """Test session validation."""
        token = "test-token"
        
        # Mock valid session
        mock_row = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "token": token,
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "ip_address": "127.0.0.1",
            "user_agent": "Test Agent"
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        session = await self.session_manager.validate_session(token)
        
        assert session is not None
        assert session.token == token
    
    @pytest.mark.asyncio
    async def test_invalidate_session(self):
        """Test session invalidation."""
        token = "test-token"
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"id": str(uuid.uuid4())}
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await self.session_manager.invalidate_session(token)
        
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        """Test expired session cleanup."""
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "DELETE 5"  # Mock 5 sessions deleted
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        deleted_count = await self.session_manager.cleanup_expired_sessions()
        
        assert deleted_count == 5
        mock_conn.execute.assert_called_once()


class TestUserRepository:
    """Test user repository operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_pool = AsyncMock()
        self.user_repository = UserRepository(self.mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_create_user(self):
        """Test user creation."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123"
        )
        hashed_password = "hashed_password"
        
        # Mock database response
        mock_row = {
            "id": str(uuid.uuid4()),
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role.value,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        user = await self.user_repository.create_user(user_data, hashed_password)
        
        assert user is not None
        assert user.username == user_data.username
        assert user.email == user_data.email
        assert user.full_name == user_data.full_name
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self):
        """Test getting user by ID."""
        user_id = str(uuid.uuid4())
        
        mock_row = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "student",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        user = await self.user_repository.get_user_by_id(user_id)
        
        assert user is not None
        assert user.id == user_id
        assert user.username == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self):
        """Test getting user by email."""
        email = "test@example.com"
        
        mock_row = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": email,
            "full_name": "Test User",
            "role": "student",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        user = await self.user_repository.get_user_by_email(email)
        
        assert user is not None
        assert user.email == email
    
    @pytest.mark.asyncio
    async def test_get_user_by_username(self):
        """Test getting user by username."""
        username = "testuser"
        
        mock_row = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "student",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        user = await self.user_repository.get_user_by_username(username)
        
        assert user is not None
        assert user.username == username
    
    @pytest.mark.asyncio
    async def test_update_user(self):
        """Test user update."""
        user_id = str(uuid.uuid4())
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com"
        )
        
        mock_row = {
            "id": user_id,
            "username": "testuser",
            "email": "updated@example.com",
            "full_name": "Updated Name",
            "role": "student",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        user = await self.user_repository.update_user(user_id, update_data)
        
        assert user is not None
        assert user.full_name == "Updated Name"
        assert user.email == "updated@example.com"
    
    @pytest.mark.asyncio
    async def test_delete_user(self):
        """Test user deletion."""
        user_id = str(uuid.uuid4())
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"id": user_id}
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await self.user_repository.delete_user(user_id)
        
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_users(self):
        """Test listing users."""
        mock_rows = [
            {
                "id": str(uuid.uuid4()),
                "username": "user1",
                "email": "user1@example.com",
                "full_name": "User One",
                "role": "student",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "username": "user2",
                "email": "user2@example.com",
                "full_name": "User Two",
                "role": "instructor",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        users = await self.user_repository.list_users()
        
        assert len(users) == 2
        assert users[0].username == "user1"
        assert users[1].username == "user2"


class TestUserService:
    """Test user service business logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user_repo = AsyncMock()
        self.mock_password_manager = Mock()
        self.mock_jwt_manager = Mock()
        self.mock_session_manager = AsyncMock()
        
        self.user_service = UserService(
            self.mock_user_repo,
            self.mock_password_manager,
            self.mock_jwt_manager,
            self.mock_session_manager
        )
    
    @pytest.mark.asyncio
    async def test_register_user(self):
        """Test user registration."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123"
        )
        
        # Mock dependencies
        self.mock_user_repo.get_user_by_email.return_value = None
        self.mock_user_repo.get_user_by_username.return_value = None
        self.mock_password_manager.hash_password.return_value = "hashed_password"
        
        mock_user = User(
            id=str(uuid.uuid4()),
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_user_repo.create_user.return_value = mock_user
        
        result = await self.user_service.register_user(user_data)
        
        assert result is not None
        assert result.username == user_data.username
        assert result.email == user_data.email
        
        # Verify dependencies were called
        self.mock_user_repo.get_user_by_email.assert_called_once_with(user_data.email)
        self.mock_user_repo.get_user_by_username.assert_called_once_with(user_data.username)
        self.mock_password_manager.hash_password.assert_called_once_with(user_data.password)
        self.mock_user_repo.create_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self):
        """Test registration with duplicate email."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123"
        )
        
        # Mock existing user
        existing_user = User(
            id=str(uuid.uuid4()),
            username="existing",
            email=user_data.email,
            full_name="Existing User",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_user_repo.get_user_by_email.return_value = existing_user
        
        with pytest.raises(HTTPException) as exc_info:
            await self.user_service.register_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self):
        """Test user authentication."""
        email = "test@example.com"
        password = "password123"
        
        mock_user = User(
            id=str(uuid.uuid4()),
            username="testuser",
            email=email,
            full_name="Test User",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock dependencies
        self.mock_user_repo.get_user_by_email.return_value = mock_user
        self.mock_user_repo.get_user_password_hash.return_value = "hashed_password"
        self.mock_password_manager.verify_password.return_value = True
        self.mock_jwt_manager.create_token.return_value = "jwt_token"
        
        mock_session = UserSession(
            id=str(uuid.uuid4()),
            user_id=mock_user.id,
            token="jwt_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        self.mock_session_manager.create_session.return_value = mock_session
        
        result = await self.user_service.authenticate_user(email, password)
        
        assert result is not None
        assert "access_token" in result
        assert "user" in result
        assert result["user"]["email"] == email
        
        # Verify dependencies were called
        self.mock_user_repo.get_user_by_email.assert_called_once_with(email)
        self.mock_password_manager.verify_password.assert_called_once_with(password, "hashed_password")
        self.mock_jwt_manager.create_token.assert_called_once()
        self.mock_session_manager.create_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        email = "test@example.com"
        password = "wrong_password"
        
        mock_user = User(
            id=str(uuid.uuid4()),
            username="testuser",
            email=email,
            full_name="Test User",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock dependencies
        self.mock_user_repo.get_user_by_email.return_value = mock_user
        self.mock_user_repo.get_user_password_hash.return_value = "hashed_password"
        self.mock_password_manager.verify_password.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            await self.user_service.authenticate_user(email, password)
        
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self):
        """Test getting user profile."""
        user_id = str(uuid.uuid4())
        
        mock_user = User(
            id=user_id,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_user_repo.get_user_by_id.return_value = mock_user
        
        result = await self.user_service.get_user_profile(user_id)
        
        assert result is not None
        assert result.id == user_id
        assert result.username == "testuser"
        
        self.mock_user_repo.get_user_by_id.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_update_user_profile(self):
        """Test updating user profile."""
        user_id = str(uuid.uuid4())
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com"
        )
        
        mock_user = User(
            id=user_id,
            username="testuser",
            email="updated@example.com",
            full_name="Updated Name",
            role=UserRole.STUDENT,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_user_repo.update_user.return_value = mock_user
        
        result = await self.user_service.update_user_profile(user_id, update_data)
        
        assert result is not None
        assert result.full_name == "Updated Name"
        assert result.email == "updated@example.com"
        
        self.mock_user_repo.update_user.assert_called_once_with(user_id, update_data)
    
    @pytest.mark.asyncio
    async def test_change_password(self):
        """Test password change."""
        user_id = str(uuid.uuid4())
        current_password = "old_password"
        new_password = "new_password123"
        
        # Mock dependencies
        self.mock_user_repo.get_user_password_hash.return_value = "old_hashed_password"
        self.mock_password_manager.verify_password.return_value = True
        self.mock_password_manager.hash_password.return_value = "new_hashed_password"
        self.mock_user_repo.update_user_password.return_value = True
        
        result = await self.user_service.change_password(user_id, current_password, new_password)
        
        assert result is True
        
        # Verify dependencies were called
        self.mock_user_repo.get_user_password_hash.assert_called_once_with(user_id)
        self.mock_password_manager.verify_password.assert_called_once_with(current_password, "old_hashed_password")
        self.mock_password_manager.hash_password.assert_called_once_with(new_password)
        self.mock_user_repo.update_user_password.assert_called_once_with(user_id, "new_hashed_password")
    
    @pytest.mark.asyncio
    async def test_logout_user(self):
        """Test user logout."""
        token = "jwt_token"
        
        self.mock_session_manager.invalidate_session.return_value = True
        
        result = await self.user_service.logout_user(token)
        
        assert result is True
        self.mock_session_manager.invalidate_session.assert_called_once_with(token)


class TestCentralizedLogging:
    """Test centralized logging integration in User Management Service."""
    
    @patch('logging_setup.setup_docker_logging')
    def test_logging_setup_called_on_service_start(self, mock_setup_logging):
        """Test that centralized logging is set up when service starts."""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Simulate service startup
        service_name = os.environ.get('SERVICE_NAME', 'user-management')
        log_level = os.environ.get('LOG_LEVEL', 'INFO')
        
        logger = mock_setup_logging(service_name, log_level)
        
        # Verify setup was called with correct parameters
        mock_setup_logging.assert_called_with(service_name, log_level)
        assert logger is not None
    
    @patch('logging_setup.setup_docker_logging')
    def test_syslog_logging_format_in_user_service(self, mock_setup_logging):
        """Test that user service uses syslog format logging."""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Setup logger
        logger = mock_setup_logging('user-management', 'INFO')
        
        # Test logging calls that would occur in user service
        logger.info("Starting User Management Service on port 8000")
        logger.info("User Management Service initialized successfully")
        logger.info("User registration successful for user: testuser")
        logger.error("Authentication failed for user: testuser")
        
        # Verify logging calls were made
        assert mock_logger.info.call_count == 3
        assert mock_logger.error.call_count == 1
        
        # Verify specific log messages
        mock_logger.info.assert_any_call("Starting User Management Service on port 8000")
        mock_logger.info.assert_any_call("User Management Service initialized successfully")
        mock_logger.info.assert_any_call("User registration successful for user: testuser")
        mock_logger.error.assert_any_call("Authentication failed for user: testuser")
    
    def test_environment_variables_for_logging(self):
        """Test that logging environment variables are properly configured."""
        with patch.dict(os.environ, {
            'DOCKER_CONTAINER': 'true',
            'SERVICE_NAME': 'user-management',
            'LOG_LEVEL': 'INFO'
        }):
            assert os.environ.get('DOCKER_CONTAINER') == 'true'
            assert os.environ.get('SERVICE_NAME') == 'user-management'
            assert os.environ.get('LOG_LEVEL') == 'INFO'
    
    @patch('logging_setup.setup_docker_logging')
    def test_logging_integration_with_user_operations(self, mock_setup_logging):
        """Test logging integration with actual user operations."""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Setup service with logging
        logger = mock_setup_logging('user-management', 'INFO')
        
        # Simulate user service operations with logging
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        # Login attempt
        logger.info(f"Login attempt for user: {email}")
        
        # Successful authentication
        logger.info(f"User authenticated successfully: {user_id}")
        
        # Profile update
        logger.info(f"User profile updated: {user_id}")
        
        # Password change
        logger.info(f"Password changed for user: {user_id}")
        
        # Session cleanup
        logger.info("Expired sessions cleaned up")
        
        # Verify all operations were logged
        assert mock_logger.info.call_count == 5
        
        # Verify specific log entries
        mock_logger.info.assert_any_call(f"Login attempt for user: {email}")
        mock_logger.info.assert_any_call(f"User authenticated successfully: {user_id}")
        mock_logger.info.assert_any_call(f"User profile updated: {user_id}")
        mock_logger.info.assert_any_call(f"Password changed for user: {user_id}")
        mock_logger.info.assert_any_call("Expired sessions cleaned up")
    
    @patch('logging_setup.setup_docker_logging')
    def test_error_logging_in_user_service(self, mock_setup_logging):
        """Test error logging in user service operations."""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        logger = mock_setup_logging('user-management', 'INFO')
        
        # Simulate various error scenarios
        error_scenarios = [
            ("Invalid email format", "ERROR"),
            ("User already exists", "WARNING"),
            ("Database connection failed", "CRITICAL"),
            ("JWT token expired", "WARNING"),
            ("Password policy violation", "WARNING")
        ]
        
        for error_msg, level in error_scenarios:
            if level == "ERROR":
                logger.error(error_msg)
            elif level == "WARNING":
                logger.warning(error_msg)
            elif level == "CRITICAL":
                logger.critical(error_msg)
        
        # Verify error logging calls
        assert mock_logger.error.call_count == 1
        assert mock_logger.warning.call_count == 3
        assert mock_logger.critical.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])