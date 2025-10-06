"""
User Service Interface - Business Logic Abstraction Layer

This module defines the abstract interfaces for user-related business operations
within the User Management Service. It separates business logic from infrastructure
concerns and provides clear contracts for user and authentication services.

Architectural Benefits:
    Interface Segregation: Separate interfaces for user and authentication concerns
    Dependency Inversion: Controllers depend on these abstractions
    Business Logic Encapsulation: Hides complex business rules behind simple interfaces
    Testability: Enables comprehensive unit testing with mocks
    Clean Architecture: Clear boundary between application and domain layers

Service Separation Rationale:
    IUserService: Focuses on user lifecycle and profile management
    IAuthenticationService: Focuses on security and credential management
    
This separation follows Single Responsibility Principle and makes the codebase
more maintainable and secure by isolating authentication concerns.

Integration with Enhanced RBAC:
    These interfaces provide the foundation for enhanced authorization through:
    - Organization-specific user management
    - Multi-tenant authentication flows
    - Role-based permission validation
    - Cross-service user identity management

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.user import User, UserRole, UserStatus

class IUserService(ABC):
    """
    Abstract interface for user business operations and lifecycle management.
    
    This interface defines the contract for user-related business logic,
    encapsulating complex operations like user creation, profile management,
    and user lifecycle operations.
    
    Business Responsibilities:
        - User creation with validation and business rules
        - Profile management and updates
        - Role and status management
        - User search and discovery
        - Data validation and business rule enforcement
    
    Security Features:
        - Username and email uniqueness validation
        - Role change authorization
        - Status management for access control
        - Secure user deletion with data integrity
    """
    
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
    """
    Abstract interface for authentication and credential management operations.
    
    This interface defines the contract for all authentication-related business
    logic, including credential validation, password management, and security
    operations.
    
    Security Responsibilities:
        - Secure password authentication
        - Password hashing and validation
        - Password reset and change operations
        - Credential verification and management
    
    Security Features:
        - Secure password hashing (bcrypt/scrypt)
        - Password strength validation
        - Secure password reset flows
        - Authentication attempt tracking
    """
    
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