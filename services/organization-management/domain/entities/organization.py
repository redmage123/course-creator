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
    
    BUSINESS REQUIREMENT:
    Organizations must provide complete contact information including
    professional contact details, physical address, and authorized
    administrator information for accountability and verification.
    
    All organization administrators must use professional email addresses
    (no Gmail, Yahoo, Hotmail, etc.) to ensure business legitimacy.
    """
    name: str
    slug: str
    # Required contact information
    address: str
    contact_phone: str  
    contact_email: str
    # Optional fields
    id: Optional[UUID] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    logo_file_path: Optional[str] = None
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
                   logo_url: str = None, logo_file_path: str = None,
                   domain: str = None, address: str = None,
                   contact_phone: str = None, contact_email: str = None,
                   settings: Dict[str, Any] = None) -> None:
        """Update organization information with professional contact details"""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if logo_url is not None:
            self.logo_url = logo_url
        if logo_file_path is not None:
            self.logo_file_path = logo_file_path
        if domain is not None:
            self.domain = domain
        if address is not None:
            self.address = address
        if contact_phone is not None:
            self.contact_phone = contact_phone
        if contact_email is not None:
            self.contact_email = contact_email
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

    def validate_contact_email(self) -> bool:
        """Validate contact email is professional (not Gmail, Yahoo, etc.)"""
        if not self.contact_email:
            return False
        
        # Import email validator
        import sys
        import os
        sys.path.append('/app/shared')
        try:
            from validation.email_validator import validate_professional_email
            result = validate_professional_email(self.contact_email)
            return result['is_valid']
        except ImportError:
            # Fallback validation if validator not available
            personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
            domain = self.contact_email.split('@')[-1].lower()
            return domain not in personal_domains

    def validate_required_fields(self) -> bool:
        """Validate all required organization fields are present"""
        return (
            bool(self.name and len(self.name.strip()) >= 2) and
            bool(self.slug and len(self.slug.strip()) >= 2) and
            bool(self.address and len(self.address.strip()) >= 10) and
            bool(self.contact_phone and len(self.contact_phone.strip()) >= 10) and
            bool(self.contact_email and '@' in self.contact_email)
        )

    def is_valid(self) -> bool:
        """Check if organization data is valid with professional requirements"""
        return (
            self.validate_required_fields() and
            self.validate_slug() and
            self.validate_domain() and
            self.validate_contact_email()
        )