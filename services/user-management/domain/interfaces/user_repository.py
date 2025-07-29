"""
User Repository Interface
Interface Segregation: Focused interface for user data access
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.user import User, UserRole, UserStatus

class IUserRepository(ABC):
    """Interface for user data access operations"""
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update user"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete user"""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username"""
        pass
    
    @abstractmethod
    async def get_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: UserStatus) -> List[User]:
        """Get users by status"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, email, or username"""
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        pass
    
    @abstractmethod
    async def count_by_role(self, role: UserRole) -> int:
        """Count users by role"""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: UserStatus) -> int:
        """Count users by status"""
        pass
    
    @abstractmethod
    async def get_recently_created(self, days: int = 7) -> List[User]:
        """Get recently created users"""
        pass
    
    @abstractmethod
    async def get_inactive_users(self, days: int = 30) -> List[User]:
        """Get users who haven't logged in for specified days"""
        pass
    
    @abstractmethod
    async def bulk_update_status(self, user_ids: List[str], status: UserStatus) -> int:
        """Bulk update user status"""
        pass