"""
Session Application Service
Single Responsibility: Manages user sessions and tokens
Dependency Inversion: Depends on abstractions for session data and token operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import secrets
import jwt
from jose import JWTError

# Repository pattern removed - using DAO
from data_access.user_dao import UserManagementDAO
from domain.interfaces.session_service import ISessionService, ITokenService
from domain.entities.session import Session, SessionStatus

class SessionService(ISessionService):
    """
    Application service for session business operations
    """
    
    def __init__(self, 
                 session_dao: UserManagementDAO,
                 token_service: ITokenService):
        self._session_dao = session_dao
        self._token_service = token_service
    
    async def create_session(self, user_id: str, session_type: str = "web", 
                           ip_address: str = None, user_agent: str = None) -> Session:
        """Create a new session"""
        if not user_id:
            raise ValueError("User ID is required")
        
        # Generate session token
        token = await self._token_service.generate_access_token(user_id, "")
        
        # Create session entity
        session = Session(
            user_id=user_id,
            token=token,
            session_type=session_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store device info if available
        if user_agent:
            device_info = self._parse_user_agent(user_agent)
            session.add_device_info(device_info)
        
        return await self._session_dao.create(session)
    
    async def get_session_by_token(self, token: str) -> Optional[Session]:
        """Get session by token"""
        return await self._session_dao.get_by_token(token)
    
    async def validate_session(self, token: str) -> Optional[Session]:
        """Validate session and return if active"""
        # For mock tokens, extract user_id and create a simple session
        if token.startswith("mock-token-"):
            # Extract user_id from token (format: mock-token-{first_8_chars})
            user_id_prefix = token.replace("mock-token-", "")
            
            # Look up the full user ID using the prefix
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Looking up user ID with prefix: {user_id_prefix}")
                
                full_user_id = await self._session_dao.get_user_id_by_prefix(user_id_prefix)
                logger.info(f"Found full user ID: {full_user_id}")
                
                if full_user_id:
                    # Create a simple session for mock tokens
                    session = Session(
                        user_id=full_user_id,
                        token=token,
                        session_type="web"
                    )
                    logger.info(f"Created session for user: {full_user_id}")
                    return session
                else:
                    logger.warning(f"No user found with prefix: {user_id_prefix}")
                    return None
            except AttributeError as e:
                # If DAO doesn't have this method, return None
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"DAO method missing: {e}")
                return None
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in session validation: {e}")
                return None
        
        # For real tokens, try database lookup
        try:
            session = await self._session_dao.get_by_token(token)
            
            if not session:
                return None
            
            # Check if session is valid
            if not session.is_valid():
                # Mark as expired if it's expired but not marked
                if session.is_expired() and session.status == SessionStatus.ACTIVE:
                    session.mark_expired()
                    await self._session_dao.update(session)
                return None
            
            # Update last accessed time
            session.update_access()
            await self._session_dao.update(session)
        except AttributeError:
            # If DAO doesn't have session methods, fall back to mock
            return None
        
        return session
    
    async def extend_session(self, token: str, duration: timedelta = None) -> Session:
        """Extend session expiration"""
        session = await self._session_dao.get_by_token(token)
        
        if not session:
            raise ValueError("Session not found")
        
        if not session.is_valid():
            raise ValueError("Cannot extend invalid session")
        
        # Use domain method to extend session
        session.extend_session(duration)
        
        return await self._session_dao.update(session)
    
    async def revoke_session(self, token: str) -> bool:
        """Revoke a specific session"""
        session = await self._session_dao.get_by_token(token)
        
        if not session:
            return False
        
        # Use domain method to revoke
        session.revoke()
        await self._session_dao.update(session)
        
        # Also revoke the token
        await self._token_service.revoke_token(token)
        
        return True
    
    async def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        sessions = await self._session_dao.get_active_by_user_id(user_id)
        
        count = 0
        for session in sessions:
            session.revoke()
            await self._session_dao.update(session)
            await self._token_service.revoke_token(session.token)
            count += 1
        
        return count
    
    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[Session]:
        """Get sessions for a user"""
        if active_only:
            return await self._session_dao.get_active_by_user_id(user_id)
        else:
            return await self._session_dao.get_by_user_id(user_id)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        return await self._session_dao.cleanup_expired()
    
    async def get_session_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        session = await self._session_dao.get_by_token(token)
        
        if not session:
            return None
        
        return {
            'session_id': session.id,
            'user_id': session.user_id,
            'session_type': session.session_type,
            'status': session.status.value,
            'created_at': session.created_at,
            'expires_at': session.expires_at,
            'last_accessed': session.last_accessed,
            'ip_address': session.ip_address,
            'device_info': session.device_info,
            'is_valid': session.is_valid(),
            'remaining_time': session.get_remaining_time()
        }
    
    async def update_session_access(self, token: str, ip_address: str = None, 
                                  user_agent: str = None) -> bool:
        """Update session access information"""
        session = await self._session_dao.get_by_token(token)
        
        if not session:
            return False
        
        session.update_access(ip_address, user_agent)
        
        # Update device info if user agent changed
        if user_agent and user_agent != session.user_agent:
            device_info = self._parse_user_agent(user_agent)
            session.add_device_info(device_info)
        
        await self._session_dao.update(session)
        return True
    
    def _parse_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """Parse user agent string to extract device info"""
        # Simplified user agent parsing
        device_info = {
            'user_agent': user_agent,
            'browser': 'unknown',
            'os': 'unknown',
            'device_type': 'desktop'
        }
        
        user_agent_lower = user_agent.lower()
        
        # Detect browser
        if 'chrome' in user_agent_lower:
            device_info['browser'] = 'Chrome'
        elif 'firefox' in user_agent_lower:
            device_info['browser'] = 'Firefox'
        elif 'safari' in user_agent_lower:
            device_info['browser'] = 'Safari'
        elif 'edge' in user_agent_lower:
            device_info['browser'] = 'Edge'
        
        # Detect OS
        if 'windows' in user_agent_lower:
            device_info['os'] = 'Windows'
        elif 'mac' in user_agent_lower:
            device_info['os'] = 'macOS'
        elif 'linux' in user_agent_lower:
            device_info['os'] = 'Linux'
        elif 'android' in user_agent_lower:
            device_info['os'] = 'Android'
            device_info['device_type'] = 'mobile'
        elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
            device_info['os'] = 'iOS'
            device_info['device_type'] = 'mobile' if 'iphone' in user_agent_lower else 'tablet'
        
        return device_info

class TokenService(ITokenService):
    """
    Service for token operations
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._revoked_tokens = set()  # In production, use Redis or database
    
    async def generate_access_token(self, user_id: str, session_id: str) -> str:
        """Generate access token"""
        payload = {
            'user_id': user_id,
            'session_id': session_id,
            'type': 'access',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'iat': datetime.now(timezone.utc),
            'jti': secrets.token_urlsafe(16)  # JWT ID for revocation
        }
        
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
    
    async def generate_refresh_token(self, user_id: str, session_id: str) -> str:
        """Generate refresh token"""
        payload = {
            'user_id': user_id,
            'session_id': session_id,
            'type': 'refresh',
            'exp': datetime.now(timezone.utc) + timedelta(days=7),
            'iat': datetime.now(timezone.utc),
            'jti': secrets.token_urlsafe(16)
        }
        
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            
            # Check if token is revoked
            if payload.get('jti') in self._revoked_tokens:
                return None
            
            return payload
        except JWTError:
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        payload = await self.verify_token(refresh_token)
        
        if not payload or payload.get('type') != 'refresh':
            return None
        
        # Generate new access token
        return await self.generate_access_token(
            payload['user_id'], 
            payload['session_id']
        )
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        payload = await self.verify_token(token)
        
        if not payload:
            return False
        
        # Add JWT ID to revoked tokens
        self._revoked_tokens.add(payload.get('jti'))
        return True