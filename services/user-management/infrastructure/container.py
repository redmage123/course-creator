"""
User Management Dependency Injection Container
Single Responsibility: Wire up dependencies and manage service lifetimes
Dependency Inversion: Configure concrete implementations for abstract interfaces
"""
import asyncpg
from typing import Optional
from omegaconf import DictConfig

# Domain interfaces
from domain.interfaces.user_repository import IUserRepository
from domain.interfaces.session_repository import ISessionRepository
from domain.interfaces.role_repository import IRoleRepository
from domain.interfaces.user_service import IUserService, IAuthenticationService
from domain.interfaces.session_service import ISessionService, ITokenService

# Application services
from application.services.user_service import UserService
from application.services.authentication_service import AuthenticationService
from application.services.session_service import SessionService, TokenService

# Infrastructure implementations
from infrastructure.repositories.postgresql_user_repository import PostgreSQLUserRepository
from infrastructure.repositories.postgresql_session_repository import PostgreSQLSessionRepository

class UserManagementContainer:
    """
    Dependency injection container following SOLID principles
    """
    
    def __init__(self, config: DictConfig):
        self._config = config
        self._connection_pool: Optional[asyncpg.Pool] = None
        
        # Repository instances (singletons)
        self._user_repository: Optional[IUserRepository] = None
        self._session_repository: Optional[ISessionRepository] = None
        self._role_repository: Optional[IRoleRepository] = None
        
        # Service instances (singletons)
        self._user_service: Optional[IUserService] = None
        self._authentication_service: Optional[IAuthenticationService] = None
        self._session_service: Optional[ISessionService] = None
        self._token_service: Optional[ITokenService] = None
    
    async def initialize(self) -> None:
        """Initialize the container and create database connections"""
        # Create database connection pool
        self._connection_pool = await asyncpg.create_pool(
            self._config.database.url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._connection_pool:
            await self._connection_pool.close()
    
    # Repository factories (following Dependency Inversion)
    def get_user_repository(self) -> IUserRepository:
        """Get user repository instance"""
        if not self._user_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            self._user_repository = PostgreSQLUserRepository(self._connection_pool)
        
        return self._user_repository
    
    def get_session_repository(self) -> ISessionRepository:
        """Get session repository instance"""
        if not self._session_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            self._session_repository = PostgreSQLSessionRepository(self._connection_pool)
        
        return self._session_repository
    
    def get_role_repository(self) -> IRoleRepository:
        """Get role repository instance"""
        if not self._role_repository:
            # For now, return a mock implementation
            # In a complete implementation, this would be:
            # self._role_repository = PostgreSQLRoleRepository(self._connection_pool)
            self._role_repository = MockRoleRepository()
        
        return self._role_repository
    
    # Service factories (following Dependency Inversion)
    def get_authentication_service(self) -> IAuthenticationService:
        """Get authentication service instance"""
        if not self._authentication_service:
            self._authentication_service = AuthenticationService(
                user_repository=self.get_user_repository()
            )
        
        return self._authentication_service
    
    def get_user_service(self) -> IUserService:
        """Get user service instance"""
        if not self._user_service:
            self._user_service = UserService(
                user_repository=self.get_user_repository(),
                auth_service=self.get_authentication_service()
            )
        
        return self._user_service
    
    def get_token_service(self) -> ITokenService:
        """Get token service instance"""
        if not self._token_service:
            # Get JWT secret from config
            jwt_secret = getattr(self._config, 'jwt_secret', 'default-secret-change-in-production')
            self._token_service = TokenService(secret_key=jwt_secret)
        
        return self._token_service
    
    def get_session_service(self) -> ISessionService:
        """Get session service instance"""
        if not self._session_service:
            self._session_service = SessionService(
                session_repository=self.get_session_repository(),
                token_service=self.get_token_service()
            )
        
        return self._session_service


# Mock implementation for demonstration (would be replaced with real PostgreSQL implementation)
class MockRoleRepository:
    """Mock role repository for demonstration"""
    
    async def create(self, role):
        return role
    
    async def get_by_id(self, role_id):
        return None
    
    async def get_by_name(self, name):
        return None
    
    async def update(self, role):
        return role
    
    async def delete(self, role_id):
        return True
    
    async def get_all(self):
        return []
    
    async def get_active_roles(self):
        return []
    
    async def get_system_roles(self):
        return []
    
    async def get_custom_roles(self):
        return []
    
    async def exists_by_name(self, name):
        return False
    
    async def get_roles_with_permission(self, permission):
        return []
    
    async def count_users_with_role(self, role_id):
        return 0