"""
User Repository Interface
"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.entities.user import User


class IUserRepository(ABC):
    """Interface for user repository operations"""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass

    @abstractmethod
    async def create_pending_user(self, email: str) -> User:
        """Create pending user for invitation"""
        pass

    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Create new user"""
        pass

    @abstractmethod
    async def update_user(self, user: User) -> User:
        """Update existing user"""
        pass

    @abstractmethod
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user"""
        pass