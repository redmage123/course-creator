"""
Token Service following Single Responsibility Principle.
Single Responsibility: Handle JWT token creation and validation.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from omegaconf import DictConfig

class ITokenService(ABC):
    """Token service interface (Interface Segregation Principle)."""
    
    @abstractmethod
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create an access token."""
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a token."""
        pass
    
    @abstractmethod
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Get token expiry time."""
        pass

class TokenService(ITokenService):
    """JWT token service implementation."""
    
    def __init__(self, security_config: DictConfig):
        """Initialize token service with security configuration."""
        self.secret_key = security_config.jwt.secret_key
        self.algorithm = security_config.jwt.algorithm
        self.access_token_expire_minutes = security_config.jwt.access_token_expire_minutes
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create an access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Get token expiry time."""
        payload = self.verify_token(token)
        if payload and "exp" in payload:
            return datetime.fromtimestamp(payload["exp"])
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired."""
        expiry = self.get_token_expiry(token)
        if expiry:
            return datetime.utcnow() > expiry
        return True