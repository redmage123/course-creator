"""
User Entity for Organization Management
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

@dataclass

class User:
    """User entity for organization management"""

    id: UUID
    email: str
    name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def is_valid(self) -> bool:
        """Validate user data"""
        return (
            self.email is not None and
            len(self.email) > 0 and
            "@" in self.email
        )

    def update_profile(self, name: Optional[str] = None):
        """Update user profile"""
        if name is not None:
            self.name = name
        self.updated_at = datetime.utcnow()

    def deactivate(self):
        """Deactivate user"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self):
        """Activate user"""
        self.is_active = True
        self.updated_at = datetime.utcnow()