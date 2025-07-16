"""
Session Repository

Database operations for session management.
"""

import logging
from typing import Dict, Any, Optional, List
import sqlalchemy
import sqlalchemy.dialects.postgresql
from datetime import datetime, timedelta
import uuid

from .base_repository import BaseRepository
from ..models.session import UserSession, SessionCreate, SessionUpdate


class SessionRepository(BaseRepository):
    """
    Repository for session data operations.
    
    Handles database operations for user session management.
    """
    
    def __init__(self, database):
        """
        Initialize session repository.
        
        Args:
            database: Database connection instance
        """
        super().__init__(database)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_tables()
    
    def _setup_tables(self):
        """Setup session-related table definitions."""
        self.user_sessions_table = sqlalchemy.Table(
            'user_sessions',
            sqlalchemy.MetaData(),
            sqlalchemy.Column('id', sqlalchemy.dialects.postgresql.UUID, 
                            primary_key=True, server_default=sqlalchemy.text('uuid_generate_v4()')),
            sqlalchemy.Column('user_id', sqlalchemy.dialects.postgresql.UUID, 
                            sqlalchemy.ForeignKey('users.id'), nullable=False),
            sqlalchemy.Column('token_hash', sqlalchemy.String(255), unique=True, nullable=False),
            sqlalchemy.Column('ip_address', sqlalchemy.String(45)),
            sqlalchemy.Column('user_agent', sqlalchemy.String(255)),
            sqlalchemy.Column('expires_at', sqlalchemy.DateTime(timezone=True), nullable=False),
            sqlalchemy.Column('created_at', sqlalchemy.DateTime(timezone=True), 
                            server_default=sqlalchemy.text('CURRENT_TIMESTAMP')),
            sqlalchemy.Column('last_accessed_at', sqlalchemy.DateTime(timezone=True), 
                            server_default=sqlalchemy.text('CURRENT_TIMESTAMP'))
        )
    
    async def create_session(self, session_data: SessionCreate, 
                           token_hash: str, expires_at: datetime) -> Optional[UserSession]:
        """
        Create a new user session.
        
        Args:
            session_data: Session creation data
            token_hash: Hashed token
            expires_at: Session expiration time
            
        Returns:
            Created session or None if creation fails
        """
        try:
            session_id = str(uuid.uuid4())
            
            # Insert new session
            insert_query = self.user_sessions_table.insert().values(
                id=session_id,
                user_id=session_data.user_id,
                token_hash=token_hash,
                ip_address=session_data.ip_address,
                user_agent=session_data.user_agent,
                expires_at=expires_at
            )
            
            await self.database.execute(insert_query)
            
            # Get the created session
            created_session = await self.get_session_by_id(session_id)
            return created_session
            
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            return None
    
    async def get_session_by_id(self, session_id: str) -> Optional[UserSession]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session or None if not found
        """
        try:
            query = self.user_sessions_table.select().where(
                self.user_sessions_table.c.id == session_id
            )
            session_data = await self.fetch_one(query)
            
            if session_data:
                return self._convert_to_session_model(session_data)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting session by ID {session_id}: {e}")
            return None
    
    async def get_active_sessions_by_user(self, user_id: str, 
                                        inactivity_timeout: timedelta) -> List[UserSession]:
        """
        Get active sessions for a user.
        
        Args:
            user_id: User ID
            inactivity_timeout: Inactivity timeout duration
            
        Returns:
            List of active sessions
        """
        try:
            cutoff_time = datetime.utcnow() - inactivity_timeout
            
            query = self.user_sessions_table.select().where(
                sqlalchemy.and_(
                    self.user_sessions_table.c.user_id == user_id,
                    self.user_sessions_table.c.last_accessed_at > cutoff_time
                )
            ).order_by(self.user_sessions_table.c.created_at.desc())
            
            sessions_data = await self.fetch_all(query)
            return [self._convert_to_session_model(session_data) for session_data in sessions_data]
            
        except Exception as e:
            self.logger.error(f"Error getting active sessions for user {user_id}: {e}")
            return []
    
    async def validate_session(self, token_hash: str, user_id: str, 
                             inactivity_timeout: timedelta) -> Optional[UserSession]:
        """
        Validate a session token.
        
        Args:
            token_hash: Hashed token
            user_id: User ID
            inactivity_timeout: Inactivity timeout duration
            
        Returns:
            Valid session or None if invalid
        """
        try:
            cutoff_time = datetime.utcnow() - inactivity_timeout
            
            query = self.user_sessions_table.select().where(
                sqlalchemy.and_(
                    self.user_sessions_table.c.user_id == user_id,
                    self.user_sessions_table.c.token_hash == token_hash,
                    self.user_sessions_table.c.last_accessed_at > cutoff_time
                )
            )
            
            session_data = await self.fetch_one(query)
            
            if session_data:
                return self._convert_to_session_model(session_data)
            return None
            
        except Exception as e:
            self.logger.error(f"Error validating session: {e}")
            return None
    
    async def update_session_access(self, session_id: str, 
                                  expires_at: datetime) -> bool:
        """
        Update session last accessed time and expiration.
        
        Args:
            session_id: Session ID
            expires_at: New expiration time
            
        Returns:
            True if successful, False otherwise
        """
        try:
            current_time = datetime.utcnow()
            
            update_query = self.user_sessions_table.update().where(
                self.user_sessions_table.c.id == session_id
            ).values(
                last_accessed_at=current_time,
                expires_at=expires_at
            )
            
            result = await self.database.execute(update_query)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error updating session access for {session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            delete_query = self.user_sessions_table.delete().where(
                self.user_sessions_table.c.id == session_id
            )
            result = await self.database.execute(delete_query)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    async def delete_session_by_token(self, token_hash: str, user_id: str) -> bool:
        """
        Delete a session by token hash.
        
        Args:
            token_hash: Hashed token
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            delete_query = self.user_sessions_table.delete().where(
                sqlalchemy.and_(
                    self.user_sessions_table.c.user_id == user_id,
                    self.user_sessions_table.c.token_hash == token_hash
                )
            )
            
            result = await self.database.execute(delete_query)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error deleting session by token: {e}")
            return False
    
    async def cleanup_old_sessions(self, user_id: str, max_sessions: int = 3) -> int:
        """
        Keep only the most recent sessions for a user.
        
        Args:
            user_id: User ID
            max_sessions: Maximum number of sessions to keep
            
        Returns:
            Number of sessions deleted
        """
        try:
            # Get sessions to keep
            keep_query = self.user_sessions_table.select().where(
                self.user_sessions_table.c.user_id == user_id
            ).order_by(self.user_sessions_table.c.created_at.desc()).limit(max_sessions)
            
            sessions_to_keep = await self.fetch_all(keep_query)
            
            if len(sessions_to_keep) >= max_sessions:
                # Get IDs of sessions to keep
                keep_ids = [str(session["id"]) for session in sessions_to_keep]
                
                # Delete sessions not in the keep list
                delete_query = self.user_sessions_table.delete().where(
                    sqlalchemy.and_(
                        self.user_sessions_table.c.user_id == user_id,
                        ~self.user_sessions_table.c.id.in_(keep_ids)
                    )
                )
                
                result = await self.database.execute(delete_query)
                return result if result else 0
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions for user {user_id}: {e}")
            return 0
    
    async def cleanup_expired_sessions(self, inactivity_timeout: timedelta) -> int:
        """
        Remove all expired sessions from database.
        
        Args:
            inactivity_timeout: Inactivity timeout duration
            
        Returns:
            Number of sessions deleted
        """
        try:
            cutoff_time = datetime.utcnow() - inactivity_timeout
            
            delete_query = self.user_sessions_table.delete().where(
                self.user_sessions_table.c.last_accessed_at < cutoff_time
            )
            
            result = await self.database.execute(delete_query)
            return result if result else 0
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def delete_all_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions deleted
        """
        try:
            delete_query = self.user_sessions_table.delete().where(
                self.user_sessions_table.c.user_id == user_id
            )
            
            result = await self.database.execute(delete_query)
            return result if result else 0
            
        except Exception as e:
            self.logger.error(f"Error deleting all sessions for user {user_id}: {e}")
            return 0
    
    async def count_active_sessions(self, inactivity_timeout: timedelta) -> int:
        """
        Count active sessions.
        
        Args:
            inactivity_timeout: Inactivity timeout duration
            
        Returns:
            Number of active sessions
        """
        try:
            cutoff_time = datetime.utcnow() - inactivity_timeout
            
            query = "SELECT COUNT(*) FROM user_sessions WHERE last_accessed_at > $1"
            return await self.fetch_val(query, cutoff_time)
            
        except Exception as e:
            self.logger.error(f"Error counting active sessions: {e}")
            return 0
    
    def _convert_to_session_model(self, session_data: dict) -> UserSession:
        """
        Convert database row to UserSession model.
        
        Args:
            session_data: Database row data
            
        Returns:
            UserSession model instance
        """
        session_dict = session_data.copy()
        session_dict['id'] = str(session_dict['id'])
        session_dict['user_id'] = str(session_dict['user_id'])
        
        # Determine if session is active based on expiration
        now = datetime.utcnow()
        session_dict['is_active'] = session_dict['expires_at'] > now
        
        return UserSession(**session_dict)