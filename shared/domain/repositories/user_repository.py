"""
User repository following SOLID principles.
Single Responsibility: Handle user data persistence operations.
"""
from typing import Optional, List
from abc import ABC, abstractmethod

from ...database.interfaces import BaseRepository, DatabaseConnection
from ..entities.user import User, UserRole

class IUserRepository(ABC):
    """User repository interface (Interface Segregation Principle)."""
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        pass
    
    @abstractmethod
    async def find_by_role(self, role: UserRole) -> List[User]:
        """Find users by role."""
        pass
    
    @abstractmethod
    async def find_active_users(self) -> List[User]:
        """Find all active users."""
        pass
    
    @abstractmethod
    async def find_by_organization(self, organization: str) -> List[User]:
        """Find users by organization."""
        pass
    
    @abstractmethod
    async def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, email, or username."""
        pass

class UserRepository(BaseRepository[User], IUserRepository):
    """Concrete user repository implementation."""
    
    def __init__(self, connection: DatabaseConnection):
        super().__init__(connection)
        self.table_name = "users"
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        query = """
        INSERT INTO users (
            id, email, username, full_name, first_name, last_name, 
            organization, hashed_password, role, is_active, is_verified,
            avatar_url, bio, created_at, updated_at
        ) VALUES (
            uuid_generate_v4(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW()
        ) RETURNING *
        """
        
        params = {
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'organization': user.organization,
            'hashed_password': user.hashed_password,
            'role': user.role.value,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'avatar_url': user.avatar_url,
            'bio': user.bio
        }
        
        results = await self.connection.execute_query(query, params)
        if results:
            return self._map_to_entity(results[0])
        
        raise RuntimeError("Failed to create user")
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = $1"
        results = await self.connection.execute_query(query, {'email': email})
        
        if results:
            return self._map_to_entity(results[0])
        return None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = "SELECT * FROM users WHERE username = $1"
        results = await self.connection.execute_query(query, {'username': username})
        
        if results:
            return self._map_to_entity(results[0])
        return None
    
    async def update(self, user: User) -> User:
        """Update an existing user."""
        query = """
        UPDATE users SET 
            email = $2, username = $3, full_name = $4, first_name = $5, 
            last_name = $6, organization = $7, role = $8, is_active = $9, 
            is_verified = $10, avatar_url = $11, bio = $12, last_login = $13,
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """
        
        params = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'organization': user.organization,
            'role': user.role.value,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'avatar_url': user.avatar_url,
            'bio': user.bio,
            'last_login': user.last_login
        }
        
        results = await self.connection.execute_query(query, params)
        if results:
            return self._map_to_entity(results[0])
        
        raise RuntimeError(f"Failed to update user with id {user.id}")
    
    async def find_by_role(self, role: UserRole) -> List[User]:
        """Find users by role."""
        query = "SELECT * FROM users WHERE role = $1 ORDER BY created_at DESC"
        results = await self.connection.execute_query(query, {'role': role.value})
        
        return [self._map_to_entity(row) for row in results]
    
    async def find_active_users(self) -> List[User]:
        """Find all active users."""
        query = "SELECT * FROM users WHERE is_active = true ORDER BY created_at DESC"
        results = await self.connection.execute_query(query)
        
        return [self._map_to_entity(row) for row in results]
    
    async def find_by_organization(self, organization: str) -> List[User]:
        """Find users by organization."""
        query = "SELECT * FROM users WHERE organization = $1 ORDER BY created_at DESC"
        results = await self.connection.execute_query(query, {'organization': organization})
        
        return [self._map_to_entity(row) for row in results]
    
    async def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, email, or username."""
        search_query = """
        SELECT * FROM users 
        WHERE (
            full_name ILIKE $1 OR 
            email ILIKE $1 OR 
            username ILIKE $1 OR
            first_name ILIKE $1 OR
            last_name ILIKE $1
        )
        ORDER BY created_at DESC
        LIMIT $2
        """
        
        search_pattern = f"%{query}%"
        params = {'pattern': search_pattern, 'limit': limit}
        results = await self.connection.execute_query(search_query, params)
        
        return [self._map_to_entity(row) for row in results]
    
    def _map_to_entity(self, row: dict) -> User:
        """Map database row to User entity."""
        user = User(
            email=row['email'],
            username=row['username'],
            full_name=row['full_name'],
            hashed_password=row['hashed_password'],
            role=UserRole(row['role']),
            first_name=row.get('first_name'),
            last_name=row.get('last_name'),
            organization=row.get('organization'),
            is_active=row.get('is_active', True),
            is_verified=row.get('is_verified', False),
            avatar_url=row.get('avatar_url'),
            bio=row.get('bio'),
            last_login=row.get('last_login')
        )
        
        user.id = row['id']
        user.created_at = row.get('created_at')
        user.updated_at = row.get('updated_at')
        
        return user