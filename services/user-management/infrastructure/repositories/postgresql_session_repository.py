"""
PostgreSQL Session Repository Implementation
Single Responsibility: Session data persistence with PostgreSQL
Dependency Inversion: Implements abstract repository interface
"""
from typing import List, Optional
from datetime import datetime
import asyncpg
import json

from domain.interfaces.session_repository import ISessionRepository
from domain.entities.session import Session, SessionStatus

class PostgreSQLSessionRepository(ISessionRepository):
    """
    PostgreSQL implementation of session repository
    """
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create(self, session: Session) -> Session:
        """Create a new session"""
        query = """
        INSERT INTO user_sessions (
            id, user_id, token, session_type, status, created_at, expires_at,
            last_accessed, ip_address, user_agent, device_info, metadata
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
        ) RETURNING *
        """
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                session.id, session.user_id, session.token, session.session_type,
                session.status.value, session.created_at, session.expires_at,
                session.last_accessed, session.ip_address, session.user_agent,
                json.dumps(session.device_info), json.dumps(session.metadata)
            )
            
            return self._row_to_session(row)
    
    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        query = "SELECT * FROM user_sessions WHERE id = $1"
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, session_id)
            
            return self._row_to_session(row) if row else None
    
    async def get_by_token(self, token: str) -> Optional[Session]:
        """Get session by token"""
        query = "SELECT * FROM user_sessions WHERE token = $1"
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, token)
            
            return self._row_to_session(row) if row else None
    
    async def get_by_user_id(self, user_id: str) -> List[Session]:
        """Get all sessions for a user"""
        query = """
        SELECT * FROM user_sessions 
        WHERE user_id = $1 
        ORDER BY last_accessed DESC
        """
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, user_id)
            
            return [self._row_to_session(row) for row in rows]
    
    async def get_active_by_user_id(self, user_id: str) -> List[Session]:
        """Get active sessions for a user"""
        query = """
        SELECT * FROM user_sessions 
        WHERE user_id = $1 AND status = 'active' AND expires_at > $2
        ORDER BY last_accessed DESC
        """
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, user_id, datetime.utcnow())
            
            return [self._row_to_session(row) for row in rows]
    
    async def update(self, session: Session) -> Session:
        """Update session"""
        query = """
        UPDATE user_sessions SET 
            status = $2, expires_at = $3, last_accessed = $4,
            ip_address = $5, user_agent = $6, device_info = $7, metadata = $8
        WHERE id = $1
        RETURNING *
        """
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                session.id, session.status.value, session.expires_at,
                session.last_accessed, session.ip_address, session.user_agent,
                json.dumps(session.device_info), json.dumps(session.metadata)
            )
            
            return self._row_to_session(row)
    
    async def delete(self, session_id: str) -> bool:
        """Delete session"""
        query = "DELETE FROM user_sessions WHERE id = $1"
        
        async with self._pool.acquire() as connection:
            result = await connection.execute(query, session_id)
            
            return result.split()[-1] == "1"
    
    async def revoke_by_user_id(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        query = """
        UPDATE user_sessions SET status = 'revoked', last_accessed = $2
        WHERE user_id = $1 AND status = 'active'
        """
        
        async with self._pool.acquire() as connection:
            result = await connection.execute(query, user_id, datetime.utcnow())
            
            return int(result.split()[-1])
    
    async def revoke_by_token(self, token: str) -> bool:
        """Revoke session by token"""
        query = """
        UPDATE user_sessions SET status = 'revoked', last_accessed = $2
        WHERE token = $1 AND status = 'active'
        """
        
        async with self._pool.acquire() as connection:
            result = await connection.execute(query, token, datetime.utcnow())
            
            return result.split()[-1] == "1"
    
    async def cleanup_expired(self) -> int:
        """Clean up expired sessions"""
        query = """
        UPDATE user_sessions SET status = 'expired'
        WHERE expires_at < $1 AND status = 'active'
        """
        
        async with self._pool.acquire() as connection:
            result = await connection.execute(query, datetime.utcnow())
            
            return int(result.split()[-1])
    
    async def get_by_status(self, status: SessionStatus) -> List[Session]:
        """Get sessions by status"""
        query = "SELECT * FROM user_sessions WHERE status = $1 ORDER BY last_accessed DESC"
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, status.value)
            
            return [self._row_to_session(row) for row in rows]
    
    async def count_active_by_user(self, user_id: str) -> int:
        """Count active sessions for a user"""
        query = """
        SELECT COUNT(*) FROM user_sessions 
        WHERE user_id = $1 AND status = 'active' AND expires_at > $2
        """
        
        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, user_id, datetime.utcnow())
    
    async def get_recent_sessions(self, user_id: str, limit: int = 10) -> List[Session]:
        """Get recent sessions for a user"""
        query = """
        SELECT * FROM user_sessions 
        WHERE user_id = $1 
        ORDER BY last_accessed DESC 
        LIMIT $2
        """
        
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, user_id, limit)
            
            return [self._row_to_session(row) for row in rows]
    
    async def extend_session(self, token: str, expires_at: datetime) -> bool:
        """Extend session expiration"""
        query = """
        UPDATE user_sessions SET expires_at = $2, last_accessed = $3
        WHERE token = $1 AND status = 'active'
        """
        
        async with self._pool.acquire() as connection:
            result = await connection.execute(query, token, expires_at, datetime.utcnow())
            
            return result.split()[-1] == "1"
    
    def _row_to_session(self, row) -> Session:
        """Convert database row to Session entity"""
        if not row:
            return None
        
        # Parse JSON fields
        device_info = json.loads(row['device_info']) if row['device_info'] else {}
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
        session = Session(
            user_id=row['user_id'],
            token=row['token'],
            session_type=row['session_type'],
            status=SessionStatus(row['status']),
            id=row['id'],
            created_at=row['created_at'],
            expires_at=row['expires_at'],
            last_accessed=row['last_accessed'],
            ip_address=row['ip_address'],
            user_agent=row['user_agent'],
            device_info=device_info,
            metadata=metadata
        )
        
        return session