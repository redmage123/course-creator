"""
Authentication Application Service
Single Responsibility: Handles authentication and password operations
Dependency Inversion: Depends on abstractions for user data and password hashing
"""
from typing import Optional
import secrets
import string
from passlib.context import CryptContext

from domain.interfaces.user_repository import IUserRepository
from domain.interfaces.user_service import IAuthenticationService
from domain.entities.user import User

class AuthenticationService(IAuthenticationService):
    """
    Application service for authentication operations
    """
    
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        if not email or not password:
            return None
        
        user = await self._user_repository.get_by_email(email)
        if not user:
            return None
        
        # Check if user is active
        if not user.is_active():
            return None
        
        # Verify password (in real implementation, password would be stored separately)
        if await self.verify_password(user.id, password):
            # Record login
            user.record_login()
            await self._user_repository.update(user)
            return user
        
        return None
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # Verify old password
        if not await self.verify_password(user_id, old_password):
            return False
        
        # Validate new password
        if not self._validate_password_strength(new_password):
            raise ValueError("Password does not meet strength requirements")
        
        # Hash and store new password
        hashed_password = await self.hash_password(new_password)
        
        # In real implementation, store password in separate secure storage
        # For now, we'll add it to user metadata (not recommended for production)
        user.add_metadata('password_hash', hashed_password)
        await self._user_repository.update(user)
        
        return True
    
    async def reset_password(self, email: str) -> str:
        """Reset password and return temporary password"""
        user = await self._user_repository.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        
        # Generate temporary password
        temp_password = self._generate_temporary_password()
        
        # Hash and store temporary password
        hashed_password = await self.hash_password(temp_password)
        user.add_metadata('password_hash', hashed_password)
        user.add_metadata('password_reset', True)
        
        await self._user_repository.update(user)
        
        return temp_password
    
    async def verify_password(self, user_id: str, password: str) -> bool:
        """Verify user password"""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # In real implementation, get password hash from secure storage
        stored_hash = user.metadata.get('password_hash')
        if not stored_hash:
            return False
        
        return self._pwd_context.verify(password, stored_hash)
    
    async def hash_password(self, password: str) -> str:
        """Hash password"""
        if not self._validate_password_strength(password):
            raise ValueError("Password does not meet strength requirements")
        
        return self._pwd_context.hash(password)
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return sum([has_upper, has_lower, has_digit, has_special]) >= 3
    
    def _generate_temporary_password(self) -> str:
        """Generate a secure temporary password"""
        length = 12
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        
        # Ensure at least one character from each category
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        
        # Fill the rest randomly
        for _ in range(length - 4):
            password.append(secrets.choice(characters))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    async def require_password_change(self, user_id: str) -> bool:
        """Mark user as requiring password change"""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            return False
        
        user.add_metadata('require_password_change', True)
        await self._user_repository.update(user)
        
        return True
    
    async def clear_password_reset_flag(self, user_id: str) -> bool:
        """Clear password reset flag after successful password change"""
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            return False
        
        user.remove_metadata('password_reset')
        user.remove_metadata('require_password_change')
        await self._user_repository.update(user)
        
        return True