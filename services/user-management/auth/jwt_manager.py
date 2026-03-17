"""
JWT Manager

Handles JWT token creation and validation.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from omegaconf import DictConfig

from models.auth import TokenPayload


class JWTManager:
    """
    JWT token management utility.
    
    Handles JWT token creation, validation, and parsing.
    """
    
    def __init__(self, config: DictConfig):
        """
        Initialize JWT manager.
        
        Args:
            config: Configuration containing JWT settings
        """
        self.secret_key = config.jwt.secret_key
        self.algorithm = config.jwt.algorithm
        self.token_expiry = config.jwt.token_expiry
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_token(self, user_id: str, role: str = None, 
                    expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT token.
        
        Args:
            user_id: User ID
            role: User role (optional)
            expires_delta: Custom expiration time (optional)
            
        Returns:
            JWT token string
        """
        try:
            # Set expiration time
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.token_expiry)
            
            # Create token payload
            payload = {
                "sub": user_id,
                "exp": expire,
                "iat": datetime.utcnow()
            }
            
            if role:
                payload["role"] = role
            
            # Encode token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
            
        except Exception as e:
            self.logger.error(f"Error creating JWT token: {e}")
            raise
    
    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Convert to TokenPayload model
            token_payload = TokenPayload(
                sub=payload["sub"],
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload.get("iat", 0)) if payload.get("iat") else None,
                role=payload.get("role")
            )
            
            return token_payload
            
        except JWTError as e:
            self.logger.warning(f"JWT decode error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error decoding JWT token: {e}")
            return None
    
    def validate_token(self, token: str) -> bool:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            payload = self.decode_token(token)
            if not payload:
                return False
            
            # Check expiration
            if payload.exp < datetime.utcnow():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating JWT token: {e}")
            return False
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get token expiration time.
        
        Args:
            token: JWT token string
            
        Returns:
            Expiration datetime or None if invalid
        """
        try:
            payload = self.decode_token(token)
            if payload:
                return payload.exp
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token expiry: {e}")
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extract user ID from token.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID or None if invalid
        """
        try:
            payload = self.decode_token(token)
            if payload:
                return payload.sub
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting user ID from token: {e}")
            return None
    
    def get_role_from_token(self, token: str) -> Optional[str]:
        """
        Extract role from token.
        
        Args:
            token: JWT token string
            
        Returns:
            Role or None if not present/invalid
        """
        try:
            payload = self.decode_token(token)
            if payload:
                return payload.role
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting role from token: {e}")
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh a JWT token.
        
        Args:
            token: Current JWT token
            
        Returns:
            New JWT token or None if refresh fails
        """
        try:
            payload = self.decode_token(token)
            if not payload:
                return None
            
            # Check if token is still valid but close to expiry
            time_until_expiry = payload.exp - datetime.utcnow()
            if time_until_expiry.total_seconds() < 300:  # Refresh if expires in 5 minutes
                return self.create_token(payload.sub, payload.role)
            
            return token  # Return original token if no refresh needed
            
        except Exception as e:
            self.logger.error(f"Error refreshing JWT token: {e}")
            return None