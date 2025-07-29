"""
User Service Interface
Interface Segregation: Focused interface for user business operations
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.user import User, UserRole, UserStatus

class IUserService(ABC):
    """Interface for user business operations"""
    
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any], password: str) -> User:
        """Create a new user with password"""
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> User:
        """Update user profile"""
        pass
    
    @abstractmethod
    async def change_user_role(self, user_id: str, new_role: UserRole) -> User:
        """Change user role"""
        pass
    
    @abstractmethod
    async def change_user_status(self, user_id: str, new_status: UserStatus) -> User:
        """Change user status"""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        pass
    
    @abstractmethod
    async def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users"""
        pass
    
    @abstractmethod
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        pass
    
    @abstractmethod
    async def get_inactive_users(self, days: int = 30) -> List[User]:
        """Get inactive users"""
        pass
    
    @abstractmethod
    async def validate_username_available(self, username: str) -> bool:
        """Check if username is available"""
        pass
    
    @abstractmethod
    async def validate_email_available(self, email: str) -> bool:
        """Check if email is available"""
        pass

class IAuthenticationService(ABC):
    """Interface for authentication operations"""
    
    @abstractmethod
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        pass
    
    @abstractmethod
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        pass
    
    @abstractmethod
    async def reset_password(self, email: str) -> str:
        """Reset password and return temporary password"""
        pass
    
    @abstractmethod
    async def verify_password(self, user_id: str, password: str) -> bool:
        """Verify user password"""
        pass
    
    @abstractmethod
    async def hash_password(self, password: str) -> str:
        """Hash password"""
        pass