"""
PostgreSQL User Repository Implementation
Single Responsibility: User data persistence with PostgreSQL
Dependency Inversion: Implements abstract repository interface
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import json

from domain.interfaces.user_repository import IUserRepository
from domain.entities.user import User, UserRole, UserStatus

class PostgreSQLUserRepository(IUserRepository):
    """
    PostgreSQL implementation of user repository
    """
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create(self, user: User) -> User:
        """Create a new user"""
        query = """
        INSERT INTO users (
            id, email, username, full_name, first_name, last_name, 
            role, status, organization, phone, timezone, language,
            profile_picture_url, bio, created_at, updated_at, metadata
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
        ) RETURNING *
        """
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query, 
                user.id, user.email, user.username, user.full_name,
                user.first_name, user.last_name, user.role.value, user.status.value,
                user.organization, user.phone, user.timezone, user.language,
                user.profile_picture_url, user.bio, user.created_at, user.updated_at,
                json.dumps(user.metadata)
            )
            
            return self._row_to_user(row)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = $1"
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, user_id)
            
            return self._row_to_user(row) if row else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = $1"
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, email)
            
            return self._row_to_user(row) if row else None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = $1"
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, username)
            
            return self._row_to_user(row) if row else None
    
    async def update(self, user: User) -> User:
        """Update user"""
        query = """
        UPDATE users SET 
            email = $2, username = $3, full_name = $4, first_name = $5, last_name = $6,
            role = $7, status = $8, organization = $9, phone = $10, timezone = $11,
            language = $12, profile_picture_url = $13, bio = $14, last_login = $15,
            updated_at = $16, metadata = $17
        WHERE id = $1
        RETURNING *
        """
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                user.id, user.email, user.username, user.full_name,
                user.first_name, user.last_name, user.role.value, user.status.value,
                user.organization, user.phone, user.timezone, user.language,
                user.profile_picture_url, user.bio, user.last_login,
                user.updated_at, json.dumps(user.metadata)
            )
            
            return self._row_to_user(row)
    
    async def delete(self, user_id: str) -> bool:
        """Delete user"""
        query = "DELETE FROM users WHERE id = $1"
        
        async with self._pool.acquire() as connection:
            result = await connection.execute(query, user_id)
            
            return result.split()[-1] == "1"  # Check if one row was affected
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)"
        
        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, email)
    
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username"""
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE username = $1)"
        
        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, username)
    
    async def get_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        query = "SELECT * FROM users WHERE role = $1 ORDER BY created_at DESC"
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, role.value)
            
            return [self._row_to_user(row) for row in rows]
    
    async def get_by_status(self, status: UserStatus) -> List[User]:
        """Get users by status"""
        query = "SELECT * FROM users WHERE status = $1 ORDER BY created_at DESC"
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, status.value)
            
            return [self._row_to_user(row) for row in rows]
    
    async def search(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, email, or username"""
        search_query = """
        SELECT * FROM users 
        WHERE full_name ILIKE $1 OR email ILIKE $1 OR username ILIKE $1
        ORDER BY 
            CASE 
                WHEN username ILIKE $1 THEN 1
                WHEN email ILIKE $1 THEN 2
                ELSE 3
            END,
            full_name
        LIMIT $2
        """
        
        search_pattern = f"%{query}%"
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(search_query, search_pattern, limit)
            
            return [self._row_to_user(row) for row in rows]
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        query = "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2"
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, limit, offset)
            
            return [self._row_to_user(row) for row in rows]
    
    async def count_by_role(self, role: UserRole) -> int:
        """Count users by role"""
        query = "SELECT COUNT(*) FROM users WHERE role = $1"
        
        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, role.value)
    
    async def count_by_status(self, status: UserStatus) -> int:
        """Count users by status"""
        query = "SELECT COUNT(*) FROM users WHERE status = $1"
        
        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, status.value)
    
    async def get_recently_created(self, days: int = 7) -> List[User]:
        """Get recently created users"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = "SELECT * FROM users WHERE created_at >= $1 ORDER BY created_at DESC"
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, cutoff_date)
            
            return [self._row_to_user(row) for row in rows]
    
    async def get_inactive_users(self, days: int = 30) -> List[User]:
        """Get users who haven't logged in for specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = """
        SELECT * FROM users 
        WHERE (last_login IS NULL OR last_login < $1) 
        AND status = 'active'
        ORDER BY last_login ASC NULLS FIRST
        """
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, cutoff_date)
            
            return [self._row_to_user(row) for row in rows]
    
    async def bulk_update_status(self, user_ids: List[str], status: UserStatus) -> int:
        """Bulk update user status"""
        query = """
        UPDATE users SET status = $1, updated_at = $2 
        WHERE id = ANY($3::text[])
        """
        
        async with self._pool.acquire() as connection:
            result = await connection.execute(
                query, 
                status.value, 
                datetime.utcnow(),
                user_ids
            )
            
            return int(result.split()[-1])  # Return number of affected rows
    
    def _row_to_user(self, row) -> User:
        """Convert database row to User entity"""
        if not row:
            return None
        
        # Parse metadata JSON
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
        user = User(
            email=row['email'],
            username=row['username'],
            full_name=row['full_name'],
            role=UserRole(row['role']),
            status=UserStatus(row['status']),
            id=row['id'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            organization=row['organization'],
            phone=row['phone'],
            timezone=row['timezone'],
            language=row['language'],
            profile_picture_url=row['profile_picture_url'],
            bio=row['bio'],
            last_login=row['last_login'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            metadata=metadata
        )
        
        return user