"""
User Application Service
Single Responsibility: Orchestrates user-related business operations
Dependency Inversion: Depends on abstractions, not concretions
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.interfaces.user_repository import IUserRepository
from domain.interfaces.user_service import IUserService, IAuthenticationService
from domain.entities.user import User, UserRole, UserStatus
from domain.entities.role import Permission

class UserService(IUserService):
    """
    Application service for user business operations
    """
    
    def __init__(self, 
                 user_repository: IUserRepository,
                 auth_service: IAuthenticationService):
        self._user_repository = user_repository
        self._auth_service = auth_service
    
    async def create_user(self, user_data: Dict[str, Any], password: str) -> User:
        """Create a new user with password"""
        # Validate required fields
        required_fields = ['email', 'username', 'full_name']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise ValueError(f"{field} is required")
        
        # Check if email is available
        if not await self.validate_email_available(user_data['email']):
            raise ValueError("Email already exists")
        
        # Check if username is available
        if not await self.validate_username_available(user_data['username']):
            raise ValueError("Username already exists")
        
        # Create user entity
        user = User(
            email=user_data['email'],
            username=user_data['username'],
            full_name=user_data['full_name'],
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            role=UserRole(user_data.get('role', 'student')),
            organization=user_data.get('organization'),
            phone=user_data.get('phone'),
            timezone=user_data.get('timezone'),
            language=user_data.get('language', 'en')
        )
        
        # Create user in repository
        created_user = await self._user_repository.create(user)
        
        # Hash and store password separately
        await self._auth_service.hash_password(password)
        
        return created_user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return await self._user_repository.get_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self._user_repository.get_by_email(email)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self._user_repository.get_by_username(username)
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> User:
        """Update user profile"""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Update profile using domain method
        user.update_profile(**profile_data)
        
        # Save updated user
        return await self._user_repository.update(user)
    
    async def change_user_role(self, user_id: str, new_role: UserRole) -> User:
        """Change user role"""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Use domain method for role change
        user.change_role(new_role)
        
        return await self._user_repository.update(user)
    
    async def change_user_status(self, user_id: str, new_status: UserStatus) -> User:
        """Change user status"""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Use domain method for status change
        user.change_status(new_status)
        
        return await self._user_repository.update(user)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # Business rule: Can't delete active admin users if they're the last admin
        if user.is_admin() and user.is_active():
            admin_count = await self._user_repository.count_by_role(UserRole.ADMIN)
            if admin_count <= 1:
                raise ValueError("Cannot delete the last admin user")
        
        return await self._user_repository.delete(user_id)
    
    async def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users"""
        if not query or len(query.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters")
        
        return await self._user_repository.search(query.strip(), limit)
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        return await self._user_repository.get_by_role(role)
    
    async def get_inactive_users(self, days: int = 30) -> List[User]:
        """Get inactive users"""
        if days < 1:
            raise ValueError("Days must be positive")
        
        return await self._user_repository.get_inactive_users(days)
    
    async def validate_username_available(self, username: str) -> bool:
        """Check if username is available"""
        return not await self._user_repository.exists_by_username(username)
    
    async def validate_email_available(self, email: str) -> bool:
        """Check if email is available"""
        return not await self._user_repository.exists_by_email(email)
    
    async def record_user_login(self, user_id: str) -> User:
        """Record user login"""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.record_login()
        return await self._user_repository.update(user)
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        total_users = len(await self._user_repository.get_all())
        active_users = await self._user_repository.count_by_status(UserStatus.ACTIVE)
        student_count = await self._user_repository.count_by_role(UserRole.STUDENT)
        instructor_count = await self._user_repository.count_by_role(UserRole.INSTRUCTOR)
        admin_count = await self._user_repository.count_by_role(UserRole.ADMIN)
        recent_users = len(await self._user_repository.get_recently_created(7))
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'students': student_count,
            'instructors': instructor_count,
            'admins': admin_count,
            'recent_signups_7_days': recent_users
        }