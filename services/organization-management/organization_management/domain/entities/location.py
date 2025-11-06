"""
Locations Entity - Geographic Training Instance Business Logic Core
Single Responsibility: Locations domain object with geographic and scheduling constraints
Dependency Inversion: No dependencies on external frameworks
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from enum import Enum


class LocationStatus(str, Enum):
    """
    Locations lifecycle status

    BUSINESS PURPOSE:
    Tracks locations through its operational lifecycle from planning to completion.

    STATUS TRANSITIONS:
    draft → active → completed (normal flow)
    draft/active → cancelled (exceptional flow)
    completed/cancelled → archived (retention flow)
    """
    DRAFT = "draft"           # Planning stage
    ACTIVE = "active"         # Currently operational
    COMPLETED = "completed"   # Training finished
    CANCELLED = "cancelled"   # Training cancelled
    ARCHIVED = "archived"     # Historical record


@dataclass
class Locations:
    """
    Locations entity representing a specific training instance at a geographic locations

    BUSINESS PURPOSE:
    Locations represent physical or virtual training sites where projects are delivered.
    Each locations has its own schedule, capacity, and custom tracks.

    EXAMPLES:
    - New York Training Center (Feb-May 2024)
    - London Office - Spring Locations
    - Remote - Q2 2024 Virtual Training

    HIERARCHY:
    Locations → Main Project → Organization

    BUSINESS RULES:
    - Each locations must reference a parent project
    - Locations have geographic context (country, region, city)
    - Start/end dates define operational period
    - Current participants cannot exceed max capacity
    - Each locations can have custom tracks
    """
    organization_id: UUID           # Required for multi-tenancy
    parent_project_id: UUID         # Main project this locations belongs to
    name: str                       # Display name (e.g., "NYC Spring 2024")
    slug: str                       # URL-safe identifier
    location_country: str           # Required - Geographic country
    timezone: str                   # Required - Timezone (e.g., "America/New_York")
    id: Optional[UUID] = None

    # Geographic details
    location_region: Optional[str] = None    # State/Province (e.g., "New York")
    location_city: Optional[str] = None      # City (e.g., "Manhattan")
    location_address: Optional[str] = None   # Full address

    # Descriptive information
    description: Optional[str] = None

    # Schedule
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_weeks: Optional[int] = None     # Auto-calculated from dates

    # Capacity management
    max_participants: Optional[int] = None
    current_participants: int = 0

    # Status and metadata
    status: LocationStatus = LocationStatus.DRAFT
    metadata: Dict[str, Any] = None          # Flexible storage for locations-specific data
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values and perform basic validation"""
        if self.id is None:
            self.id = uuid4()
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def update_info(self, name: str = None, description: str = None,
                   location_country: str = None, location_region: str = None,
                   location_city: str = None, location_address: str = None,
                   timezone: str = None, start_date: date = None,
                   end_date: date = None, max_participants: int = None,
                   metadata: Dict[str, Any] = None) -> None:
        """
        Update locations information

        BUSINESS PURPOSE:
        Allows org admins to update locations details while maintaining audit trail.

        WHY THIS APPROACH:
        - Optional parameters allow partial updates
        - Only non-None values are updated (preserves existing data)
        - updated_at timestamp automatically set
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if location_country is not None:
            self.location_country = location_country
        if location_region is not None:
            self.location_region = location_region
        if location_city is not None:
            self.location_city = location_city
        if location_address is not None:
            self.location_address = location_address
        if timezone is not None:
            self.timezone = timezone
        if start_date is not None:
            self.start_date = start_date
        if end_date is not None:
            self.end_date = end_date
        if max_participants is not None:
            self.max_participants = max_participants
        if metadata is not None:
            self.metadata = metadata
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """
        Activate locations for training operations

        BUSINESS PURPOSE:
        Transitions locations from planning (draft) to operational (active) state.

        BUSINESS RULES:
        - Can only activate from DRAFT status
        - Must pass validation checks before activation
        """
        if self.status == LocationStatus.DRAFT and self.is_valid():
            self.status = LocationStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """
        Mark locations as completed (training finished)

        BUSINESS PURPOSE:
        Closes locations after all training activities are done.
        """
        if self.status == LocationStatus.ACTIVE:
            self.status = LocationStatus.COMPLETED
            self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """
        Cancel locations training

        BUSINESS PURPOSE:
        Allows org admins to cancel planned or active locations.
        """
        if self.status in [LocationStatus.DRAFT, LocationStatus.ACTIVE]:
            self.status = LocationStatus.CANCELLED
            self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """
        Archive locations for historical records

        BUSINESS PURPOSE:
        Moves completed or cancelled locations to archived state.
        """
        if self.status in [LocationStatus.COMPLETED, LocationStatus.CANCELLED]:
            self.status = LocationStatus.ARCHIVED
            self.updated_at = datetime.utcnow()

    def validate_slug(self) -> bool:
        """
        Validate slug format

        BUSINESS RULE:
        Slug must be lowercase alphanumeric with hyphens only
        """
        import re
        return bool(re.match(r'^[a-z0-9-]+$', self.slug))

    def validate_dates(self) -> bool:
        """
        Validate date constraints

        BUSINESS RULE:
        If both dates provided, start_date must be <= end_date
        """
        if self.start_date is not None and self.end_date is not None:
            return self.start_date <= self.end_date
        return True

    def validate_capacity(self) -> bool:
        """
        Validate capacity constraints

        BUSINESS RULES:
        - Current participants cannot exceed max capacity
        - Current participants must be non-negative
        """
        if self.current_participants < 0:
            return False
        if self.max_participants is not None:
            return self.current_participants <= self.max_participants
        return True

    def validate_timezone(self) -> bool:
        """
        Validate timezone format

        BUSINESS RULE:
        Timezone must follow IANA timezone database format
        """
        # Basic validation - timezone should not be empty
        # Full validation would require pytz, but basic check is sufficient
        return bool(self.timezone and len(self.timezone.strip()) > 0)

    def is_valid(self) -> bool:
        """
        Check if locations data is valid for activation

        BUSINESS PURPOSE:
        Validates all business rules before allowing locations activation.
        """
        return (
            bool(self.name and len(self.name.strip()) >= 2) and
            bool(self.slug and len(self.slug.strip()) >= 2) and
            bool(self.location_country and len(self.location_country.strip()) >= 2) and
            self.validate_slug() and
            self.validate_dates() and
            self.validate_capacity() and
            self.validate_timezone()
        )

    def can_activate(self) -> bool:
        """Check if locations can be activated"""
        return self.status == LocationStatus.DRAFT and self.is_valid()

    def is_active(self) -> bool:
        """Check if locations is currently active"""
        return self.status == LocationStatus.ACTIVE

    def is_operational(self) -> bool:
        """Check if locations is accepting participants"""
        return self.status == LocationStatus.ACTIVE

    def has_capacity(self) -> bool:
        """
        Check if locations has available capacity

        BUSINESS PURPOSE:
        Determines if new participants can be added to locations.
        """
        if self.max_participants is None:
            return True  # No limit set
        return self.current_participants < self.max_participants

    def get_available_capacity(self) -> Optional[int]:
        """Get remaining capacity"""
        if self.max_participants is None:
            return None
        return max(0, self.max_participants - self.current_participants)

    def get_capacity_percentage(self) -> Optional[float]:
        """
        Get capacity utilization percentage

        BUSINESS PURPOSE:
        Used for dashboard displays and capacity planning.
        """
        if self.max_participants is None or self.max_participants == 0:
            return None
        return (self.current_participants / self.max_participants) * 100

    def increment_participants(self, count: int = 1) -> bool:
        """
        Add participants to locations

        BUSINESS PURPOSE:
        Updates participant count when students enroll.

        Returns:
            bool: True if successful, False if would exceed capacity
        """
        if self.max_participants is not None:
            if self.current_participants + count > self.max_participants:
                return False
        self.current_participants += count
        self.updated_at = datetime.utcnow()
        return True

    def decrement_participants(self, count: int = 1) -> bool:
        """
        Remove participants from locations

        BUSINESS PURPOSE:
        Updates participant count when students withdraw.

        Returns:
            bool: True if successful, False if would go negative
        """
        if self.current_participants - count < 0:
            return False
        self.current_participants -= count
        self.updated_at = datetime.utcnow()
        return True

    def get_location_display(self) -> str:
        """
        Get formatted locations string for display

        BUSINESS PURPOSE:
        Provides human-readable locations description for UI.

        Examples:
        - "New York, United States"
        - "Manhattan, New York, United States"
        - "London, United Kingdom"
        """
        parts = []
        if self.location_city:
            parts.append(self.location_city)
        if self.location_region:
            parts.append(self.location_region)
        parts.append(self.location_country)
        return ", ".join(parts)

    def calculate_duration_weeks(self) -> Optional[int]:
        """
        Calculate duration in weeks from start and end dates

        BUSINESS PURPOSE:
        Auto-calculates duration for display and scheduling.

        WHY THIS APPROACH:
        - Returns None if dates not set
        - Rounds up to nearest week
        - Used by database trigger to auto-populate duration_weeks
        """
        if self.start_date is None or self.end_date is None:
            return None
        days = (self.end_date - self.start_date).days
        return (days + 6) // 7  # Round up to nearest week
