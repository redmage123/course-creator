"""
Password generator service for creating secure random passwords.
Following SOLID principles.
"""
import random
import string
from typing import Optional


class PasswordGenerator:
    """
    Service for generating secure random passwords.
    Follows Single Responsibility Principle - only handles password generation.
    """
    
    def __init__(
        self,
        min_length: int = 12,
        max_length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_special: bool = True,
        special_chars: str = "!@#$%^&*"
    ):
        """
        Initialize password generator with configuration.
        
        Args:
            min_length: Minimum password length
            max_length: Maximum password length
            include_uppercase: Include uppercase letters
            include_lowercase: Include lowercase letters
            include_digits: Include digits
            include_special: Include special characters
            special_chars: String of allowed special characters
        """
        self.min_length = min_length
        self.max_length = max_length
        self.include_uppercase = include_uppercase
        self.include_lowercase = include_lowercase
        self.include_digits = include_digits
        self.include_special = include_special
        self.special_chars = special_chars
        
        # Build character set
        self.char_set = self._build_character_set()
        
        if not self.char_set:
            raise ValueError("At least one character type must be enabled")
    
    def _build_character_set(self) -> str:
        """
        Build the character set for password generation.
        
        Returns:
            str: Available characters for password generation
        """
        chars = ""
        
        if self.include_lowercase:
            chars += string.ascii_lowercase
        
        if self.include_uppercase:
            chars += string.ascii_uppercase
        
        if self.include_digits:
            chars += string.digits
        
        if self.include_special:
            chars += self.special_chars
        
        return chars
    
    def generate_password(self, length: Optional[int] = None) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Specific length for password (if None, uses random length within range)
            
        Returns:
            str: Generated password
        """
        if length is None:
            length = random.randint(self.min_length, self.max_length)
        
        if length < self.min_length or length > self.max_length:
            raise ValueError(f"Password length must be between {self.min_length} and {self.max_length}")
        
        # Ensure at least one character from each enabled category
        password = []
        
        if self.include_lowercase:
            password.append(random.choice(string.ascii_lowercase))
        
        if self.include_uppercase:
            password.append(random.choice(string.ascii_uppercase))
        
        if self.include_digits:
            password.append(random.choice(string.digits))
        
        if self.include_special:
            password.append(random.choice(self.special_chars))
        
        # Fill remaining length with random characters from full set
        remaining_length = length - len(password)
        for _ in range(remaining_length):
            password.append(random.choice(self.char_set))
        
        # Shuffle the password to avoid predictable patterns
        random.shuffle(password)
        
        return ''.join(password)
    
    def validate_password(self, password: str) -> bool:
        """
        Validate that a password meets the configured requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            bool: True if password meets requirements, False otherwise
        """
        if len(password) < self.min_length or len(password) > self.max_length:
            return False
        
        if self.include_lowercase and not any(c in string.ascii_lowercase for c in password):
            return False
        
        if self.include_uppercase and not any(c in string.ascii_uppercase for c in password):
            return False
        
        if self.include_digits and not any(c in string.digits for c in password):
            return False
        
        if self.include_special and not any(c in self.special_chars for c in password):
            return False
        
        return True