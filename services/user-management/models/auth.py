"""
Authentication Models

Pydantic models for authentication operations.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    """JWT token model."""
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Login request model."""
    username: str  # Can be email or username
    password: str


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr
    new_password: str


class TokenPayload(BaseModel):
    """JWT token payload model."""
    sub: str  # User ID
    exp: datetime
    iat: Optional[datetime] = None
    role: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    user: dict
    expires_at: datetime
    session_id: str


class ValidateResponse(BaseModel):
    """Session validation response model."""
    valid: bool
    user_id: str
    email: str
    expires_at: datetime
    message: str