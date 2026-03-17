"""
Password Manager

Handles password hashing and verification.
"""

import logging
from passlib.context import CryptContext
from typing import Optional


class PasswordManager:
    """
    Password management utility.
    
    Handles password hashing and verification using bcrypt.
    """
    
    def __init__(self):
        """Initialize password manager."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            self.logger.error(f"Error hashing password: {e}")
            raise
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return self.pwd_context.verify(password, hashed_password)
        except Exception as e:
            self.logger.error(f"Error verifying password: {e}")
            return False
    
    def needs_update(self, hashed_password: str) -> bool:
        """
        Check if password hash needs updating.
        
        Args:
            hashed_password: Hashed password
            
        Returns:
            True if hash needs updating, False otherwise
        """
        try:
            return self.pwd_context.needs_update(hashed_password)
        except Exception as e:
            self.logger.error(f"Error checking if password needs update: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> dict:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Validation result with strength info
        """
        try:
            result = {
                "valid": True,
                "errors": [],
                "strength": "weak"
            }
            
            # Check minimum length
            if len(password) < 8:
                result["valid"] = False
                result["errors"].append("Password must be at least 8 characters long")
            
            # Check for uppercase
            if not any(c.isupper() for c in password):
                result["errors"].append("Password should contain at least one uppercase letter")
            
            # Check for lowercase
            if not any(c.islower() for c in password):
                result["errors"].append("Password should contain at least one lowercase letter")
            
            # Check for digits
            if not any(c.isdigit() for c in password):
                result["errors"].append("Password should contain at least one digit")
            
            # Check for special characters
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                result["errors"].append("Password should contain at least one special character")
            
            # Determine strength
            if len(result["errors"]) == 0:
                result["strength"] = "strong"
            elif len(result["errors"]) <= 2:
                result["strength"] = "medium"
            else:
                result["strength"] = "weak"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating password strength: {e}")
            return {
                "valid": False,
                "errors": ["Password validation failed"],
                "strength": "unknown"
            }