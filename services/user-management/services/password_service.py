"""
Password Service following Single Responsibility Principle.
Single Responsibility: Handle password hashing and verification.
"""
from abc import ABC, abstractmethod
from passlib.context import CryptContext
from omegaconf import DictConfig

class IPasswordService(ABC):
    """Password service interface (Interface Segregation Principle)."""
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a plain text password."""
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        pass

class PasswordService(IPasswordService):
    """Concrete password service implementation."""
    
    def __init__(self, security_config: DictConfig):
        """Initialize password service with security configuration."""
        self.pwd_context = CryptContext(
            schemes=security_config.get("password_schemes", ["bcrypt"]),
            deprecated="auto"
        )
    
    def hash_password(self, password: str) -> str:
        """Hash a plain text password."""
        if not password:
            raise ValueError("Password cannot be empty")
        
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        if not plain_password or not hashed_password:
            return False
        
        return self.pwd_context.verify(plain_password, hashed_password)