"""
User Repository

Database operations for user management.
"""

import logging
from typing import Dict, Any, Optional, List
import sqlalchemy
import sqlalchemy.dialects.postgresql
from datetime import datetime

from .base_repository import BaseRepository
from ..models.user import User, UserCreate, UserUpdate, UserRole


class UserRepository(BaseRepository):
    """
    Repository for user data operations.
    
    Handles database operations for user management.
    """
    
    def __init__(self, database):
        """
        Initialize user repository.
        
        Args:
            database: Database connection instance
        """
        super().__init__(database)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_tables()
    
    def _setup_tables(self):
        """Setup user-related table definitions."""
        self.users_table = sqlalchemy.Table(
            'users',
            sqlalchemy.MetaData(),
            sqlalchemy.Column('id', sqlalchemy.dialects.postgresql.UUID, 
                            primary_key=True, server_default=sqlalchemy.text('uuid_generate_v4()')),
            sqlalchemy.Column('email', sqlalchemy.String(255), unique=True, nullable=False),
            sqlalchemy.Column('username', sqlalchemy.String(100), unique=True, nullable=False),
            sqlalchemy.Column('full_name', sqlalchemy.String(255), nullable=False),
            sqlalchemy.Column('hashed_password', sqlalchemy.String(255), nullable=False),
            sqlalchemy.Column('is_active', sqlalchemy.Boolean, default=True),
            sqlalchemy.Column('is_verified', sqlalchemy.Boolean, default=False),
            sqlalchemy.Column('role', sqlalchemy.String(50), default='student'),
            sqlalchemy.Column('avatar_url', sqlalchemy.Text),
            sqlalchemy.Column('bio', sqlalchemy.Text),
            sqlalchemy.Column('created_at', sqlalchemy.DateTime(timezone=True), 
                            server_default=sqlalchemy.text('CURRENT_TIMESTAMP')),
            sqlalchemy.Column('updated_at', sqlalchemy.DateTime(timezone=True), 
                            server_default=sqlalchemy.text('CURRENT_TIMESTAMP')),
            sqlalchemy.Column('last_login', sqlalchemy.DateTime(timezone=True))
        )
    
    async def create_user(self, user_data: UserCreate, hashed_password: str) -> Optional[User]:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            hashed_password: Hashed password
            
        Returns:
            Created user or None if creation fails
        """
        try:
            # Use provided username or create from email
            username = user_data.username or user_data.email.split('@')[0]
            
            # Check if email already exists
            if await self.get_user_by_email(user_data.email):
                raise ValueError("Email already registered")
            
            # Check if username already exists
            if await self.get_user_by_username(username):
                raise ValueError("Username already taken")
            
            # Insert new user
            insert_query = self.users_table.insert().values(
                email=user_data.email,
                username=username,
                full_name=user_data.full_name or "",
                hashed_password=hashed_password,
                is_active=True,
                is_verified=False,
                role='student'
            )
            
            await self.database.execute(insert_query)
            
            # Get the created user
            created_user = await self.get_user_by_email(user_data.email)
            return created_user
            
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
            query = self.users_table.select().where(self.users_table.c.id == user_id)
            user_data = await self.fetch_one(query)
            
            if user_data:
                return self._convert_to_user_model(user_data)
            return None
            
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
            query = self.users_table.select().where(self.users_table.c.email == email)
            user_data = await self.fetch_one(query)
            
            if user_data:
                return self._convert_to_user_model(user_data)
            return None
            
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
            query = self.users_table.select().where(self.users_table.c.username == username)
            user_data = await self.fetch_one(query)
            
            if user_data:
                return self._convert_to_user_model(user_data)
            return None
            
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
            # Build update data
            update_data = {}
            if updates.email is not None:
                update_data['email'] = updates.email
            if updates.full_name is not None:
                update_data['full_name'] = updates.full_name
            if updates.is_active is not None:
                update_data['is_active'] = updates.is_active
            if updates.role is not None:
                update_data['role'] = updates.role
            
            if update_data:
                update_data['updated_at'] = datetime.utcnow()
                update_query = self.users_table.update().where(
                    self.users_table.c.id == user_id
                ).values(**update_data)
                await self.database.execute(update_query)
            
            # Get updated user
            return await self.get_user_by_id(user_id)
            
        except Exception as e:
            self.logger.error(f"Error updating user {user_id}: {e}")
            return None
    
    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        """
        Update user password.
        
        Args:
            user_id: User ID
            hashed_password: New hashed password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_query = self.users_table.update().where(
                self.users_table.c.id == user_id
            ).values(
                hashed_password=hashed_password,
                updated_at=datetime.utcnow()
            )
            
            result = await self.database.execute(update_query)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error updating password for user {user_id}: {e}")
            return False
    
    async def update_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_query = self.users_table.update().where(
                self.users_table.c.id == user_id
            ).values(last_login=datetime.utcnow())
            
            result = await self.database.execute(update_query)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error updating last login for user {user_id}: {e}")
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
            delete_query = self.users_table.delete().where(self.users_table.c.id == user_id)
            result = await self.database.execute(delete_query)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        List all users with pagination.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of users
        """
        try:
            query = self.users_table.select().limit(limit).offset(offset).order_by(
                self.users_table.c.created_at.desc()
            )
            users_data = await self.fetch_all(query)
            
            return [self._convert_to_user_model(user_data) for user_data in users_data]
            
        except Exception as e:
            self.logger.error(f"Error listing users: {e}")
            return []
    
    async def count_users(self) -> int:
        """
        Count total number of users.
        
        Returns:
            Total user count
        """
        try:
            query = "SELECT COUNT(*) FROM users"
            return await self.fetch_val(query)
            
        except Exception as e:
            self.logger.error(f"Error counting users: {e}")
            return 0
    
    async def count_active_users(self) -> int:
        """
        Count active users.
        
        Returns:
            Active user count
        """
        try:
            query = "SELECT COUNT(*) FROM users WHERE is_active = true"
            return await self.fetch_val(query)
            
        except Exception as e:
            self.logger.error(f"Error counting active users: {e}")
            return 0
    
    async def count_users_by_role(self, role: str) -> int:
        """
        Count users by role.
        
        Args:
            role: User role
            
        Returns:
            User count for role
        """
        try:
            query = "SELECT COUNT(*) FROM users WHERE role = $1"
            return await self.fetch_val(query, role)
            
        except Exception as e:
            self.logger.error(f"Error counting users by role {role}: {e}")
            return 0
    
    async def search_users(self, search_term: str, limit: int = 100) -> List[User]:
        """
        Search users by email, username, or full name.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        try:
            query = self.users_table.select().where(
                sqlalchemy.or_(
                    self.users_table.c.email.ilike(f"%{search_term}%"),
                    self.users_table.c.username.ilike(f"%{search_term}%"),
                    self.users_table.c.full_name.ilike(f"%{search_term}%")
                )
            ).limit(limit)
            
            users_data = await self.fetch_all(query)
            return [self._convert_to_user_model(user_data) for user_data in users_data]
            
        except Exception as e:
            self.logger.error(f"Error searching users: {e}")
            return []
    
    def _convert_to_user_model(self, user_data: dict) -> User:
        """
        Convert database row to User model.
        
        Args:
            user_data: Database row data
            
        Returns:
            User model instance
        """
        user_dict = user_data.copy()
        user_dict['id'] = str(user_dict['id'])
        user_dict['roles'] = [user_dict.get('role', 'student')]
        return User(**user_dict)