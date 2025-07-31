"""
Organization Entity - Business Logic Core
Single Responsibility: Organization domain object with business rules
Dependency Inversion: No dependencies on external frameworks
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from enum import Enum

@dataclass

class Organization:
    """
    Organization entity representing a training institution or company
    """
    name: str
    slug: str
    id: Optional[UUID] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    domain: Optional[str] = None
    settings: Dict[str, Any] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.settings is None:
            self.settings = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def update_info(self, name: str = None, description: str = None,
                   logo_url: str = None, domain: str = None,
                   settings: Dict[str, Any] = None) -> None:
        """Update organization information"""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if logo_url is not None:
            self.logo_url = logo_url
        if domain is not None:
            self.domain = domain
        if settings is not None:
            self.settings = settings
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate organization"""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate organization"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def validate_slug(self) -> bool:
        """Validate slug format"""
        import re
        return bool(re.match(r'^[a-z0-9-]+$', self.slug))

    def validate_domain(self) -> bool:
        """Validate domain format"""
        if not self.domain:
            return True
        import re
        return bool(re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.domain))

    def is_valid(self) -> bool:
        """Check if organization data is valid"""
        return (
            bool(self.name and len(self.name.strip()) >= 2) and
            bool(self.slug and len(self.slug.strip()) >= 2) and
            self.validate_slug() and
            self.validate_domain()
        )