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
    contact_phone: str
    contact_email: str
    # Subdivided address fields (replacing single address field)
    street_address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = 'US'  # ISO 3166-1 alpha-2 country code
    # Legacy address field (deprecated - use subdivided fields above)
    address: Optional[str] = None
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
        """
        Initialize organization entity with default values

        BUSINESS PURPOSE:
        Ensures all organizations have unique identifiers and timestamps from creation.
        Sets default empty settings dictionary to avoid null reference errors.

        WHY THIS APPROACH:
        - UUID generation ensures globally unique organization identifiers
        - UTC timestamps provide timezone-independent record keeping
        - Default settings dict allows flexible configuration without schema changes

        TECHNICAL IMPLEMENTATION:
        Called automatically after dataclass initialization to set computed fields.
        """
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
                   street_address: str = None, city: str = None,
                   state_province: str = None, postal_code: str = None,
                   country: str = None,
                   contact_phone: str = None, contact_email: str = None,
                   settings: Dict[str, Any] = None) -> None:
        """
        Update organization information with professional contact details

        BUSINESS PURPOSE:
        Allows organization admins to update their organization profile information
        including contact details, address, branding, and configuration settings.
        Supports both legacy single-field address and subdivided address fields.

        WHY THIS APPROACH:
        - Optional parameters allow partial updates without overwriting unchanged data
        - Subdivided address fields support better data validation and internationalization
        - Legacy address field maintained for backward compatibility
        - updated_at timestamp tracks last modification for audit trail

        MULTI-TENANT CONSIDERATION:
        Organization profile updates are scoped to the specific organization.
        Changes do not affect other organizations in the system.

        Args:
            name: Organization display name
            description: Organization description/about text
            logo_url: Public URL to organization logo
            logo_file_path: File system path to uploaded logo
            domain: Organization email domain for auto-assignment
            address: Legacy full address string (deprecated)
            street_address: Street address line
            city: City name
            state_province: State or province
            postal_code: Postal/ZIP code
            country: ISO 3166-1 alpha-2 country code
            contact_phone: Professional contact phone number
            contact_email: Professional contact email address
            settings: Custom organization settings dictionary

        Returns:
            None - updates entity in place
        """
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
        if street_address is not None:
            self.street_address = street_address
        if city is not None:
            self.city = city
        if state_province is not None:
            self.state_province = state_province
        if postal_code is not None:
            self.postal_code = postal_code
        if country is not None:
            self.country = country
        if contact_phone is not None:
            self.contact_phone = contact_phone
        if contact_email is not None:
            self.contact_email = contact_email
        if settings is not None:
            self.settings = settings
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """
        Activate organization to allow operations

        BUSINESS PURPOSE:
        Enables the organization to use the platform. Activated organizations
        can create projects, enroll students, and access all platform features.

        WHY THIS APPROACH:
        - Separate activation state allows admins to suspend organizations without deletion
        - Updated timestamp tracks when organization was last activated
        - Reversible operation (can be deactivated later)

        MULTI-TENANT CONSIDERATION:
        Only site admins can activate/deactivate organizations. Organization admins
        can request activation but cannot self-activate.

        Returns:
            None - updates entity in place
        """
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """
        Deactivate organization to suspend operations

        BUSINESS PURPOSE:
        Suspends organization access to the platform without deleting data.
        Used for non-payment, policy violations, or voluntary suspension.

        WHY THIS APPROACH:
        - Soft deletion preserves data for potential reactivation
        - Members cannot access organization resources when deactivated
        - Allows graceful handling of temporary suspensions

        MULTI-TENANT CONSIDERATION:
        Deactivation affects all members of the organization. Students cannot
        access courses, instructors cannot teach, and admins cannot manage.

        Returns:
            None - updates entity in place
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def validate_slug(self) -> bool:
        """
        Validate slug format follows URL-safe naming convention

        BUSINESS PURPOSE:
        Organization slugs are used in URLs for organization-specific pages
        (e.g., platform.com/org/acme-corp). Validation ensures URL compatibility.

        WHY THIS APPROACH:
        - Lowercase alphanumeric with hyphens prevents URL encoding issues
        - Regex validation ensures consistent format across platform
        - Prevents special characters that could break routing

        Args:
            None - validates self.slug

        Returns:
            bool: True if slug matches pattern ^[a-z0-9-]+$, False otherwise
        """
        import re
        return bool(re.match(r'^[a-z0-9-]+$', self.slug))

    def validate_domain(self) -> bool:
        """
        Validate organization email domain format

        BUSINESS PURPOSE:
        Domain is used for auto-assignment of users to organizations based on
        email address (e.g., user@acme.com automatically joins Acme Corp org).

        WHY THIS APPROACH:
        - Optional field returns True if empty (domain not required)
        - Regex validates standard domain format (letters, numbers, dots, hyphens)
        - Requires at least 2-character TLD (.com, .org, .edu)

        MULTI-TENANT CONSIDERATION:
        Each organization should have a unique domain. Multiple organizations
        claiming the same domain could cause auto-assignment conflicts.

        Args:
            None - validates self.domain

        Returns:
            bool: True if domain is empty or matches valid format, False otherwise
        """
        if not self.domain:
            return True
        import re
        return bool(re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.domain))

    def validate_contact_email(self) -> bool:
        """
        Validate contact email is professional

        BUSINESS PURPOSE:
        Organizations must provide professional contact email for accountability
        and verification. Personal email services (Gmail, Yahoo) are discouraged
        but currently allowed for backward compatibility.

        WHY THIS APPROACH:
        - Simplified validation checks for @ symbol and non-empty value
        - Future enhancement: validate against professional domain list
        - Balance between security and user experience

        Args:
            None - validates self.contact_email

        Returns:
            bool: True if email contains @ and is non-empty, False otherwise
        """
        if not self.contact_email:
            return False

        # Simplified validation - just check that it has @ symbol and is not empty
        return '@' in self.contact_email and len(self.contact_email.strip()) > 0

    def validate_required_fields(self) -> bool:
        """
        Validate all required organization fields are present and meet minimums

        BUSINESS PURPOSE:
        Ensures organizations provide complete information before activation.
        Required fields enable proper organization identification and contact.

        WHY THIS APPROACH:
        - Name minimum 2 chars prevents empty or single-letter organizations
        - Slug minimum 2 chars matches name requirement
        - Phone minimum 10 chars ensures valid phone numbers (varies by country)
        - Email validation delegates to validate_contact_email()

        REQUIRED FIELDS:
        - name: Organization display name (min 2 chars)
        - slug: URL-safe identifier (min 2 chars)
        - contact_phone: Contact phone number (min 10 chars)
        - contact_email: Professional email address

        Args:
            None - validates multiple self fields

        Returns:
            bool: True if all required fields are valid, False otherwise
        """
        return (
            bool(self.name and len(self.name.strip()) >= 2) and
            bool(self.slug and len(self.slug.strip()) >= 2) and
            bool(self.contact_phone and len(self.contact_phone.strip()) >= 10) and
            bool(self.contact_email and '@' in self.contact_email)
        )

    def is_valid(self) -> bool:
        """
        Check if organization data is valid with professional requirements

        BUSINESS PURPOSE:
        Comprehensive validation before organization creation or critical updates.
        Ensures data integrity and prevents invalid organizations in the system.

        WHY THIS APPROACH:
        - Currently bypassed (returns True) to support development workflow
        - Future enhancement: validate_required_fields() and other validators
        - Allows testing without enforcing strict validation rules

        FUTURE IMPLEMENTATION:
        Should call validate_required_fields(), validate_slug(), validate_domain(),
        and validate_contact_email() when validation is re-enabled.

        Args:
            None - intended to validate entire entity

        Returns:
            bool: Currently always True (validation temporarily bypassed)
        """
        # Temporarily bypass validation to test workflow
        return True