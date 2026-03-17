"""
Authentication Models

Pydantic models for authentication operations.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    """JWT token model."""
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    """
    Single source of truth for login requests.
    
    CONSOLIDATED MODEL: This replaces all other login models in the codebase.
    Accepts both username and email for backward compatibility.
    """
    username: str = Field(..., description="Username or email address for authentication")
    password: str = Field(..., description="User password")


class PasswordResetRequest(BaseModel):
    """
    DEPRECATED: Use PasswordResetRequestModel instead.
    This model is kept for backward compatibility only.
    """
    email: EmailStr
    new_password: str


class PasswordResetRequestModel(BaseModel):
    """
    Request model for initiating password reset flow.

    Security Context:
    Implements OWASP password reset best practices with no user enumeration.
    Returns generic success message regardless of email validity.
    """
    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordResetVerifyRequest(BaseModel):
    """
    Request model for verifying password reset token validity.

    Security Context:
    Validates token before allowing password change form to be displayed.
    Implements time-based token expiration (1-hour window).
    """
    token: str = Field(..., min_length=32, max_length=64, description="Password reset token")


class PasswordResetCompleteRequest(BaseModel):
    """
    Request model for completing password reset with new password.

    Security Context:
    - Validates token and password strength
    - Implements single-use tokens (auto-invalidated after success)
    - Enforces password strength requirements (min 8 chars, 3 of 4 character types)
    - Uses bcrypt hashing with automatic salt generation
    """
    token: str = Field(..., min_length=32, max_length=64, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class PasswordResetRequestResponse(BaseModel):
    """Response for password reset request."""
    message: str
    success: bool


class PasswordResetVerifyResponse(BaseModel):
    """Response for password reset token verification."""
    valid: bool
    user_id: Optional[str] = None
    error: Optional[str] = None


class PasswordResetCompleteResponse(BaseModel):
    """Response for password reset completion."""
    success: bool
    message: str


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