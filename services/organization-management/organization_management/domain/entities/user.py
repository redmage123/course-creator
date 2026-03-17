"""
User Entity for Organization Management
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

@dataclass
class User:
    """
    User entity for organization management

    BUSINESS PURPOSE:
    Represents a user account in the organization management context. Users can have
    multiple roles across different organizations (multi-tenant membership).

    TECHNICAL NOTE:
    This is a lightweight domain entity focused on user identity. Full user details
    (authentication, password, roles) are managed by the user-management service.

    MULTI-TENANT CONSIDERATION:
    A single user can belong to multiple organizations with different roles in each.
    The user entity itself is organization-agnostic; organization memberships are
    tracked separately via OrganizationMembership entities.

    Attributes:
        id: Unique user identifier (UUID)
        email: User email address (unique across platform)
        name: User display name (optional for privacy)
        is_active: Whether user account is active (soft deletion)
        created_at: Account creation timestamp (UTC)
        updated_at: Last modification timestamp (UTC)
    """

    id: UUID
    email: str
    name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        """
        Initialize user entity with default values

        BUSINESS PURPOSE:
        Ensures all users have unique identifiers and timestamps from creation.

        WHY THIS APPROACH:
        - UUID generation ensures globally unique user identifiers
        - UTC timestamps provide timezone-independent record keeping
        - Separate created_at and updated_at enable audit trail

        TECHNICAL IMPLEMENTATION:
        Called automatically after dataclass initialization to set computed fields.
        """
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def is_valid(self) -> bool:
        """
        Validate user data meets minimum requirements

        BUSINESS PURPOSE:
        Ensures user has a valid email address before creation or updates.
        Email is the primary identifier for authentication and communication.

        WHY THIS APPROACH:
        - Simplified validation checks for @ symbol and non-empty value
        - Email uniqueness enforced at database level, not domain level
        - Balance between security and user experience

        VALIDATION RULES:
        - Email must not be null
        - Email must not be empty string
        - Email must contain @ symbol (basic format check)

        Args:
            None - validates self.email

        Returns:
            bool: True if email is valid, False otherwise
        """
        return (
            self.email is not None and
            len(self.email) > 0 and
            "@" in self.email
        )

    def update_profile(self, name: Optional[str] = None):
        """
        Update user profile information

        BUSINESS PURPOSE:
        Allows users to update their display name. Email updates are handled
        separately through authentication service for security verification.

        WHY THIS APPROACH:
        - Optional parameter allows partial updates
        - updated_at timestamp tracks last modification for audit trail
        - Name is optional to support privacy preferences

        MULTI-TENANT CONSIDERATION:
        Name change applies across all organizations. If user is "John Smith" in
        one org, they are "John Smith" in all orgs (single identity).

        Args:
            name: User display name (optional)

        Returns:
            None - updates entity in place
        """
        if name is not None:
            self.name = name
        self.updated_at = datetime.utcnow()

    def deactivate(self):
        """
        Deactivate user account

        BUSINESS PURPOSE:
        Soft deletion that suspends user access without deleting data.
        Used for voluntary account closure, policy violations, or security threats.

        WHY THIS APPROACH:
        - Preserves user data for audit trail and potential reactivation
        - Prevents login while maintaining data integrity
        - Reversible operation (can be reactivated later)

        MULTI-TENANT CONSIDERATION:
        Deactivation affects all organization memberships. User cannot access
        any organization they belong to when deactivated.

        SECURITY IMPLICATION:
        Deactivated users cannot log in, but their data remains in the system.
        Use for temporary suspensions, not GDPR deletion requests.

        Returns:
            None - updates entity in place
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self):
        """
        Activate user account

        BUSINESS PURPOSE:
        Enables user access to the platform. Used for account creation,
        reactivation after suspension, or manual approval workflows.

        WHY THIS APPROACH:
        - Separate activation state allows admins to control access
        - Updated timestamp tracks when user was last activated
        - Reversible operation (can be deactivated later)

        MULTI-TENANT CONSIDERATION:
        Activation restores access to all organization memberships. User can
        immediately access all organizations they belong to.

        Returns:
            None - updates entity in place
        """
        self.is_active = True
        self.updated_at = datetime.utcnow()