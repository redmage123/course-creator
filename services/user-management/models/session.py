"""
Session Models

Pydantic models for user session management.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserSession(BaseModel):
    """User session model."""
    id: str
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    last_accessed_at: datetime
    is_active: bool = True


class SessionInfo(BaseModel):
    """Session information model."""
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    last_accessed_at: datetime
    expires_at: datetime
    is_current: bool = False


class SessionCreate(BaseModel):
    """Session creation model."""
    user_id: str
    token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SessionUpdate(BaseModel):
    """Session update model."""
    last_accessed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class SessionListResponse(BaseModel):
    """Session list response model."""
    sessions: list[SessionInfo]
    count: int