"""
User Service

Business logic for user management operations.
"""

import logging
from typing import Optional, List, Dict, Any

from repositories.user_repository import UserRepository
from models.user import User, UserCreate, UserUpdate, UserProfile, UserStats
from auth.password_manager import PasswordManager


class UserService:
    """
    Service for user management operations.
    
    Handles business logic for user-related operations.
    """
    
    def __init__(self, user_repository: UserRepository, password_manager: PasswordManager):
        """
        Initialize user service.
        
        Args:
            user_repository: User repository
            password_manager: Password manager
        """
        self.user_repository = user_repository
        self.password_manager = password_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def create_user(self, user_data: UserCreate) -> Optional[User]:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user or None if creation fails
        """
        try:
            # Validate password strength
            password_validation = self.password_manager.validate_password_strength(
                user_data.password
            )
            
            if not password_validation["valid"]:
                raise ValueError(f"Password validation failed: {password_validation['errors']}")
            
            # Hash password
            hashed_password = self.password_manager.hash_password(user_data.password)
            
            # Create user
            user = await self.user_repository.create_user(user_data, hashed_password)
            
            if user:
                self.logger.info(f"User created successfully: {user.email}")
                return user
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User or None if not found
        """
        try:
            return await self.user_repository.get_user_by_id(user_id)
            
        except Exception as e:
            self.logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User or None if not found
        """
        try:
            return await self.user_repository.get_user_by_email(email)
            
        except Exception as e:
            self.logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User or None if not found
        """
        try:
            return await self.user_repository.get_user_by_username(username)
            
        except Exception as e:
            self.logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    async def update_user(self, user_id: str, updates: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            updates: Updates to apply
            
        Returns:
            Updated user or None if not found
        """
        try:
            # Validate email uniqueness if email is being updated
            if updates.email:
                existing_user = await self.user_repository.get_user_by_email(updates.email)
                if existing_user and existing_user.id != user_id:
                    raise ValueError("Email already in use by another user")
            
            # Update user
            user = await self.user_repository.update_user(user_id, updates)
            
            if user:
                self.logger.info(f"User updated successfully: {user.email}")
                return user
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Verify old password
            if not self.password_manager.verify_password(old_password, user.hashed_password):
                raise ValueError("Current password is incorrect")
            
            # Validate new password strength
            password_validation = self.password_manager.validate_password_strength(new_password)
            if not password_validation["valid"]:
                raise ValueError(f"Password validation failed: {password_validation['errors']}")
            
            # Hash new password
            hashed_password = self.password_manager.hash_password(new_password)
            
            # Update password
            success = await self.user_repository.update_password(user_id, hashed_password)
            
            if success:
                self.logger.info(f"Password changed for user {user.email}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error changing password for user {user_id}: {e}")
            raise
    
    async def reset_password(self, email: str, new_password: str) -> bool:
        """
        Reset user password (admin function).
        
        Args:
            email: User email
            new_password: New password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user
            user = await self.user_repository.get_user_by_email(email)
            if not user:
                raise ValueError("User not found")
            
            # Validate new password strength
            password_validation = self.password_manager.validate_password_strength(new_password)
            if not password_validation["valid"]:
                raise ValueError(f"Password validation failed: {password_validation['errors']}")
            
            # Hash new password
            hashed_password = self.password_manager.hash_password(new_password)
            
            # Update password
            success = await self.user_repository.update_password(user.id, hashed_password)
            
            if success:
                self.logger.info(f"Password reset for user {user.email}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error resetting password for user {email}: {e}")
            raise
    
    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            updates = UserUpdate(is_active=False)
            user = await self.user_repository.update_user(user_id, updates)
            
            if user:
                self.logger.info(f"User deactivated: {user.email}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error deactivating user {user_id}: {e}")
            return False
    
    async def activate_user(self, user_id: str) -> bool:
        """
        Activate a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            updates = UserUpdate(is_active=True)
            user = await self.user_repository.update_user(user_id, updates)
            
            if user:
                self.logger.info(f"User activated: {user.email}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error activating user {user_id}: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user for logging
            user = await self.user_repository.get_user_by_id(user_id)
            
            # Delete user
            success = await self.user_repository.delete_user(user_id)
            
            if success and user:
                self.logger.info(f"User deleted: {user.email}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        List users with pagination.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of users
        """
        try:
            return await self.user_repository.list_users(limit, offset)
            
        except Exception as e:
            self.logger.error(f"Error listing users: {e}")
            return []
    
    async def search_users(self, search_term: str, limit: int = 100) -> List[User]:
        """
        Search users.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        try:
            return await self.user_repository.search_users(search_term, limit)
            
        except Exception as e:
            self.logger.error(f"Error searching users: {e}")
            return []
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile or None if not found
        """
        try:
            user = await self.user_repository.get_user_by_id(user_id)
            if user:
                return UserProfile(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name,
                    role=user.role,
                    avatar_url=user.avatar_url,
                    bio=user.bio,
                    created_at=user.created_at
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user profile {user_id}: {e}")
            return None
    
    async def get_user_stats(self) -> UserStats:
        """
        Get user statistics.
        
        Returns:
            User statistics
        """
        try:
            total_users = await self.user_repository.count_users()
            active_users = await self.user_repository.count_active_users()
            
            admin_count = await self.user_repository.count_users_by_role("admin")
            instructor_count = await self.user_repository.count_users_by_role("instructor")
            student_count = await self.user_repository.count_users_by_role("student")
            
            return UserStats(
                total_users=total_users,
                active_users=active_users,
                users_by_role={
                    "admin": admin_count,
                    "instructor": instructor_count,
                    "student": student_count
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting user stats: {e}")
            return UserStats(
                total_users=0,
                active_users=0,
                users_by_role={"admin": 0, "instructor": 0, "student": 0}
            )
    
    async def update_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.user_repository.update_last_login(user_id)
            
        except Exception as e:
            self.logger.error(f"Error updating last login for user {user_id}: {e}")
            return False
    
    async def validate_user_credentials(self, email: str, password: str) -> Optional[User]:
        """
        Validate user credentials.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User if credentials are valid, None otherwise
        """
        try:
            user = await self.user_repository.get_user_by_email(email)
            if not user:
                return None
            
            # Verify password
            if not self.password_manager.verify_password(password, user.hashed_password):
                return None
            
            return user
            
        except Exception as e:
            self.logger.error(f"Error validating credentials for {email}: {e}")
            return None