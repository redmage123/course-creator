"""
User Application Service - User Account Management and Business Operations

This module implements the user management business logic for the User Management
Service, providing comprehensive user account CRUD operations, role management,
profile updates, and user-related business workflows.

Service Architecture:
    Application Layer Service: Orchestrates user business logic
    Domain Service Implementation: Implements IUserService interface
    Business Logic Focus: User account lifecycle and management
    Dependency Injection: Uses DAO and authentication service abstractions

Core User Features:
    - User account creation and validation
    - User profile management and updates
    - User role and status management
    - User search and filtering
    - User statistics and analytics
    - Custom user ID support
    - Email/username uniqueness validation

Business Logic Implementation:
    - User registration workflows
    - Profile update validations
    - Role change authorization
    - Account deletion rules (prevent last admin deletion)
    - Inactive user identification
    - User search and discovery
    - User statistics reporting

Integration Points:
    - User DAO: User data persistence and retrieval
    - Authentication Service: Password hashing and validation
    - Session Service: User session management (indirect)
    - Email Service: User notifications (future enhancement)
    - Analytics Service: User activity tracking (future)

Security Considerations:
    - Password hashing before storage
    - Email/username uniqueness enforcement
    - Custom user ID validation
    - Account status verification
    - Role-based access control enforcement
    - Last admin protection (prevents lockout)

Design Patterns Applied:
    - Service Layer Pattern: Encapsulates user business logic
    - Repository Pattern: DAO abstraction for data access
    - Dependency Injection: Testable and maintainable dependencies
    - Domain Entity Pattern: User entity with business rules

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

# Repository pattern removed - using DAO
from data_access.user_dao import UserManagementDAO
from user_management.domain.interfaces.user_service import IUserService, IAuthenticationService
from user_management.domain.entities.user import User, UserRole, UserStatus
from user_management.domain.entities.role import Permission

class UserService(IUserService):
    """
    User Service Implementation - User Account Management

    This service implements comprehensive user management functionality for the
    Course Creator Platform. It provides production-ready user account operations
    with validation, security, and business rule enforcement.

    Service Responsibilities:
        - User account creation and registration
        - User profile management and updates
        - User role and status management
        - Email/username availability validation
        - Custom user ID support and validation
        - User search and discovery
        - User statistics and reporting
        - Account deletion with business rules

    Business Rules:
        - Email addresses must be unique across platform
        - Usernames must be unique across platform
        - Custom user IDs must be unique if provided
        - Cannot delete last admin user (prevents lockout)
        - Password must be hashed before storage
        - Search queries must be at least 2 characters

    Integration Features:
        - DAO pattern for user persistence
        - Authentication service for password operations
        - Domain entity integration for user management
        - Extensible for future user-related features

    Usage Examples:
        # Create user with auto-generated ID
        user = await user_service.create_user(
            user_data={
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "role": "student"
            },
            password="SecurePass123!"
        )

        # Create user with custom ID
        user = await user_service.create_user(
            user_data={
                "user_id": "custom-123",
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe"
            },
            password="SecurePass123!"
        )

        # Update user profile
        updated_user = await user_service.update_user_profile(
            user_id="user-123",
            profile_data={"phone": "+1234567890", "timezone": "America/New_York"}
        )

        # Search users
        users = await user_service.search_users("john", limit=20)
    """

    def __init__(self,
                 user_dao: UserManagementDAO,
                 auth_service: IAuthenticationService):
        """
        Initialize user service with required dependencies.

        Args:
            user_dao (UserManagementDAO): DAO for user data access
            auth_service (IAuthenticationService): Service for password operations
        """
        self._user_dao = user_dao
        self._auth_service = auth_service
    
    async def validate_user_id_available(self, user_id: str) -> bool:
        """
        Check if custom user ID is available.
        
        Business Context:
        User ID uniqueness validation ensures data integrity when users
        specify custom IDs during registration, preventing conflicts.
        """
        return not await self._user_dao.exists_by_id(user_id)

    async def create_user(self, user_data: Dict[str, Any], password: str) -> User:
        """
        Create a new user with password and optional custom user ID validation.
        
        Business Context:
        User creation supports both auto-generated and custom user IDs. When a custom
        user ID is provided, the system validates its uniqueness before proceeding
        with account creation to maintain data integrity.
        """
        # Validate required fields
        required_fields = ['email', 'username', 'full_name']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise ValueError(f"{field} is required")
        
        # Check if custom user ID is provided and validate uniqueness
        if 'user_id' in user_data and user_data['user_id']:
            if not await self.validate_user_id_available(user_data['user_id']):
                raise ValueError("User ID already exists")
        
        # Check if email is available
        if not await self.validate_email_available(user_data['email']):
            raise ValueError("Email already exists")
        
        # Check if username is available
        if not await self.validate_username_available(user_data['username']):
            raise ValueError("Username already exists")
        
        # Create user entity with optional custom ID
        # BUSINESS RULE: New users default to organization_admin role
        # Instructors are assigned by organization admins and linked to organizations
        user_init_data = {
            'email': user_data['email'],
            'username': user_data['username'],
            'full_name': user_data['full_name'],
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'role': UserRole(user_data.get('role', 'organization_admin')),
            'organization': user_data.get('organization'),
            'phone': user_data.get('phone'),
            'timezone': user_data.get('timezone'),
            'language': user_data.get('language', 'en')
        }
        
        # Only pass ID if it's provided
        if user_data.get('user_id'):
            user_init_data['id'] = user_data['user_id']
            
        user = User(**user_init_data)
        
        # Hash password before creating user
        hashed_password = await self._auth_service.hash_password(password)
        
        # Prepare user data dictionary for DAO
        user_data_for_dao = {
            'user_id': user.id,  # Custom user ID if provided
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'hashed_password': hashed_password,
            'role': user.role.value,  # Extract enum value
            'organization': user.organization,
            'phone': user.phone,
            'timezone': user.timezone,
            'language': user.language,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'status': user.status.value  # Extract enum value
        }
        
        # Create user in DAO and get the User object
        created_user = await self._user_dao.create(user_data_for_dao)
        
        return created_user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve user by unique identifier.

        Args:
            user_id (str): Unique user identifier

        Returns:
            Optional[User]: User entity if found, None otherwise
        """
        return await self._user_dao.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email address.

        Args:
            email (str): User's email address

        Returns:
            Optional[User]: User entity if found, None otherwise
        """
        return await self._user_dao.get_by_email(email)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve user by username.

        Args:
            username (str): User's username

        Returns:
            Optional[User]: User entity if found, None otherwise
        """
        return await self._user_dao.get_by_username(username)
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> User:
        """
        Update user profile information.

        Business Context:
            Updates user profile fields such as name, phone, timezone, language.
            Uses domain entity's update_profile method for validation.

        Args:
            user_id (str): Unique user identifier
            profile_data (Dict[str, Any]): Profile fields to update

        Returns:
            User: Updated user entity

        Raises:
            ValueError: If user not found
        """
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Update profile using domain method
        user.update_profile(**profile_data)
        
        # Save updated user
        return await self._user_dao.update(user)
    
    async def change_user_role(self, user_id: str, new_role: UserRole) -> User:
        """
        Change user's role (e.g., student to instructor).

        Business Context:
            Updates user's role for RBAC. Should be performed by authorized admins only.

        Args:
            user_id (str): User identifier
            new_role (UserRole): New role to assign

        Returns:
            User: Updated user entity

        Raises:
            ValueError: If user not found
        """
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Use domain method for role change
        user.change_role(new_role)
        
        return await self._user_dao.update(user)
    
    async def change_user_status(self, user_id: str, new_status: UserStatus) -> User:
        """
        Change user's account status (active, inactive, suspended).

        Business Context:
            Controls user access. Inactive/suspended users cannot authenticate.

        Args:
            user_id (str): User identifier
            new_status (UserStatus): New status to assign

        Returns:
            User: Updated user entity

        Raises:
            ValueError: If user not found
        """
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Use domain method for status change
        user.change_status(new_status)
        
        return await self._user_dao.update(user)
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user account with business rule validation.

        Business Context:
            Permanently deletes user account. CRITICAL BUSINESS RULE: Cannot delete
            last admin user to prevent platform lockout.

        Args:
            user_id (str): User identifier to delete

        Returns:
            bool: True if deleted successfully, False if user not found

        Raises:
            ValueError: If attempting to delete last admin user
        """
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            return False
        
        # Business rule: Can't delete active admin users if they're the last admin
        if user.is_admin() and user.is_active():
            admin_count = await self._user_dao.count_by_role(UserRole.ADMIN)
            if admin_count <= 1:
                raise ValueError("Cannot delete the last admin user")
        
        return await self._user_dao.delete(user_id)
    
    async def search_users(self, query: str, limit: int = 50) -> List[User]:
        """
        Search users by name, email, or username.

        Business Context:
            Enables user discovery for admin dashboards and user management UIs.

        Args:
            query (str): Search query (minimum 2 characters)
            limit (int): Maximum results to return. Defaults to 50

        Returns:
            List[User]: Matching users

        Raises:
            ValueError: If query less than 2 characters
        """
        if not query or len(query.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters")
        
        return await self._user_dao.search(query.strip(), limit)
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """
        Retrieve all users with specific role.

        Args:
            role (UserRole): Role to filter by

        Returns:
            List[User]: Users with the specified role
        """
        return await self._user_dao.get_by_role(role)
    
    async def get_inactive_users(self, days: int = 30) -> List[User]:
        """
        Retrieve users inactive for specified number of days.

        Business Context:
            Used for user engagement campaigns or account cleanup.

        Args:
            days (int): Number of days of inactivity. Defaults to 30

        Returns:
            List[User]: Inactive users

        Raises:
            ValueError: If days is less than 1
        """
        if days < 1:
            raise ValueError("Days must be positive")
        
        return await self._user_dao.get_inactive_users(days)
    
    async def validate_username_available(self, username: str) -> bool:
        """
        Check if username is available for registration.

        Args:
            username (str): Username to check

        Returns:
            bool: True if available, False if taken
        """
        return not await self._user_dao.exists_by_username(username)

    async def validate_email_available(self, email: str) -> bool:
        """
        Check if email is available for registration.

        Args:
            email (str): Email address to check

        Returns:
            bool: True if available, False if taken
        """
        return not await self._user_dao.exists_by_email(email)
    
    async def record_user_login(self, user_id: str) -> User:
        """
        Update user's last login timestamp.

        Business Context:
            Called after successful authentication to track user activity.

        Args:
            user_id (str): User identifier

        Returns:
            User: Updated user entity

        Raises:
            ValueError: If user not found
        """
        user = await self._user_dao.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.record_login()
        return await self._user_dao.update(user)
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Retrieve platform-wide user statistics.

        Business Context:
            Provides analytics data for admin dashboards showing user counts,
            activity metrics, and growth trends.

        Returns:
            Dict[str, Any]: User statistics including total, active, by role, etc.
        """
        total_users = len(await self._user_dao.get_all())
        active_users = await self._user_dao.count_by_status(UserStatus.ACTIVE)
        student_count = await self._user_dao.count_by_role(UserRole.STUDENT)
        instructor_count = await self._user_dao.count_by_role(UserRole.INSTRUCTOR)
        admin_count = await self._user_dao.count_by_role(UserRole.ADMIN)
        recent_users = len(await self._user_dao.get_recently_created(7))
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'students': student_count,
            'instructors': instructor_count,
            'admins': admin_count,
            'recent_signups_7_days': recent_users
        }