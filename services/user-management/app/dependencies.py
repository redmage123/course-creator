"""
User Management Service Dependencies.
Dependency Inversion Principle: Depend on abstractions, not concretions.
"""
from fastapi import FastAPI
from omegaconf import DictConfig
import sys
from pathlib import Path

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.database.postgresql import PostgreSQLFactory
from shared.domain.repositories.user_repository import UserRepository, IUserRepository
from services.auth_service import AuthService, IAuthService
from services.user_service import UserService, IUserService
from services.password_service import PasswordService, IPasswordService
from services.token_service import TokenService, ITokenService

class UserManagementDependencyContainer:
    """Container for managing user management service dependencies."""
    
    def __init__(self, config: DictConfig):
        self.config = config
        self._services = {}
        self._repositories = {}
        self._db_factory = None
    
    def get_database_factory(self) -> PostgreSQLFactory:
        """Get database factory instance."""
        if not self._db_factory:
            connection_string = self.config.database.connection_string
            self._db_factory = PostgreSQLFactory(connection_string)
        return self._db_factory
    
    def get_user_repository(self) -> IUserRepository:
        """Get user repository instance."""
        if 'user_repository' not in self._repositories:
            db_factory = self.get_database_factory()
            connection = db_factory.create_connection()
            self._repositories['user_repository'] = UserRepository(connection)
        return self._repositories['user_repository']
    
    def get_password_service(self) -> IPasswordService:
        """Get password service instance."""
        if 'password_service' not in self._services:
            self._services['password_service'] = PasswordService(self.config.security)
        return self._services['password_service']
    
    def get_token_service(self) -> ITokenService:
        """Get token service instance."""
        if 'token_service' not in self._services:
            self._services['token_service'] = TokenService(self.config.security)
        return self._services['token_service']
    
    def get_user_service(self) -> IUserService:
        """Get user service instance."""
        if 'user_service' not in self._services:
            user_repo = self.get_user_repository()
            password_service = self.get_password_service()
            self._services['user_service'] = UserService(user_repo, password_service)
        return self._services['user_service']
    
    def get_auth_service(self) -> IAuthService:
        """Get authentication service instance."""
        if 'auth_service' not in self._services:
            user_service = self.get_user_service()
            token_service = self.get_token_service()
            password_service = self.get_password_service()
            self._services['auth_service'] = AuthService(
                user_service, token_service, password_service
            )
        return self._services['auth_service']

# Global container instance
_container: UserManagementDependencyContainer = None

def setup_dependencies(app: FastAPI, config: DictConfig) -> None:
    """Setup dependency injection container."""
    global _container
    _container = UserManagementDependencyContainer(config)
    
    # Store container in app state for access in routes
    app.state.container = _container

def get_container() -> UserManagementDependencyContainer:
    """Get the global dependency container."""
    if not _container:
        raise RuntimeError("Dependencies not initialized")
    return _container