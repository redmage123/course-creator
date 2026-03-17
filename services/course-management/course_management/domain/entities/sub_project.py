"""
Sub-Project Domain Entity

BUSINESS CONTEXT:
Represents a specific instance (locations) of a main project in a particular
locations with customized scheduling. Sub-projects enable multi-locations
training programs where the same curriculum runs in different cities/regions
with independent schedules and capacity.

DOMAIN MODEL:
Sub-projects are child entities of projects in a hierarchical structure.
Each sub-project has its own locations, dates, capacity, and status.

@module sub_project_entity
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


@dataclass
class SubProject:
    """
    Sub-Project (Locations) Domain Entity

    BUSINESS VALUE:
    - Enables running the same training program in multiple locations
    - Provides independent scheduling per locations
    - Tracks capacity separately per locations
    - Supports lifecycle management (draft → active → completed)

    ATTRIBUTES:
    - id: Unique identifier for the sub-project
    - parent_project_id: Reference to the main project (template)
    - organization_id: Organization owning this locations
    - name: Human-readable name (e.g., "Boston Locations Fall 2025")
    - slug: URL-friendly identifier (e.g., "boston-fall-2025")
    - description: Detailed description of the locations
    - location_country: ISO country name (e.g., "United States")
    - location_region: State/Province (e.g., "Massachusetts")
    - location_city: City name (e.g., "Boston")
    - location_address: Physical address (optional)
    - timezone: IANA timezone (e.g., "America/New_York")
    - start_date: Locations start date
    - end_date: Locations end date
    - duration_weeks: Calculated duration in weeks
    - max_participants: Maximum enrollment capacity
    - current_participants: Current enrollment count
    - status: Lifecycle status (draft, active, completed, cancelled, archived)
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    - created_by: Creator user ID
    - updated_by: Last updater user ID
    - metadata: Flexible JSON storage for additional data
    """

    # Identification
    id: UUID = field(default_factory=uuid4)
    parent_project_id: UUID = field(default=None)
    organization_id: UUID = field(default=None)

    # Basic Info
    name: str = ""
    slug: str = ""
    description: Optional[str] = None

    # Locations
    location_country: str = ""
    location_region: Optional[str] = None
    location_city: Optional[str] = None
    location_address: Optional[str] = None
    timezone: str = "UTC"

    # Schedule
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_weeks: Optional[int] = None

    # Capacity
    max_participants: Optional[int] = None
    current_participants: int = 0

    # Status
    status: str = "draft"

    # Audit
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    # Flexible storage
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Valid status values
    VALID_STATUSES = ['draft', 'active', 'completed', 'cancelled', 'archived']

    def __post_init__(self):
        """Validate entity after initialization"""
        self.validate()

    def validate(self) -> None:
        """
        Validate sub-project entity

        BUSINESS RULES:
        - Name is required
        - Locations country is required
        - Timezone is required
        - Status must be valid
        - Dates must be logical (start <= end)
        - Capacity must be non-negative

        Raises:
            ValueError: If validation fails
        """
        if not self.name:
            raise ValueError("Sub-project name is required")

        if not self.location_country:
            raise ValueError("Locations country is required")

        if not self.timezone:
            raise ValueError("Timezone is required")

        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {self.VALID_STATUSES}")

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date must be before or equal to end date")

        if self.current_participants < 0:
            raise ValueError("Current participants cannot be negative")

        if self.max_participants is not None and self.max_participants < 0:
            raise ValueError("Max participants cannot be negative")

        if (self.max_participants is not None and
            self.current_participants > self.max_participants):
            raise ValueError("Current participants cannot exceed max participants")

    def is_at_capacity(self) -> bool:
        """
        Check if sub-project is at maximum capacity

        Returns:
            True if at capacity, False otherwise
        """
        if self.max_participants is None:
            return False  # No limit
        return self.current_participants >= self.max_participants

    def has_available_slots(self, count: int = 1) -> bool:
        """
        Check if sub-project has available slots for enrollment

        Args:
            count: Number of slots needed

        Returns:
            True if has available slots, False otherwise
        """
        if self.max_participants is None:
            return True  # No limit
        return (self.current_participants + count) <= self.max_participants

    def increment_participants(self, count: int = 1) -> None:
        """
        Increment participant count

        Args:
            count: Number to increment by

        Raises:
            ValueError: If would exceed capacity
        """
        if not self.has_available_slots(count):
            raise ValueError(f"Cannot add {count} participants - would exceed capacity")
        self.current_participants += count

    def decrement_participants(self, count: int = 1) -> None:
        """
        Decrement participant count

        Args:
            count: Number to decrement by

        Raises:
            ValueError: If would go below zero
        """
        if self.current_participants - count < 0:
            raise ValueError("Cannot decrement participants below zero")
        self.current_participants -= count

    def calculate_capacity_percentage(self) -> float:
        """
        Calculate current capacity as percentage

        Returns:
            Percentage (0-100) or 0 if no max limit
        """
        if self.max_participants is None or self.max_participants == 0:
            return 0.0
        return (self.current_participants / self.max_participants) * 100.0

    def can_transition_to(self, new_status: str) -> bool:
        """
        Check if status transition is valid

        BUSINESS RULES:
        - draft → active
        - active → completed
        - active → cancelled
        - completed → archived
        - Any status can transition to archived

        Args:
            new_status: Target status

        Returns:
            True if transition is valid, False otherwise
        """
        if new_status not in self.VALID_STATUSES:
            return False

        # Can always archive
        if new_status == 'archived':
            return True

        # Define valid transitions
        valid_transitions = {
            'draft': ['active', 'cancelled'],
            'active': ['completed', 'cancelled'],
            'completed': ['archived'],
            'cancelled': ['archived'],
            'archived': []  # Terminal state
        }

        return new_status in valid_transitions.get(self.status, [])

    def transition_to(self, new_status: str) -> None:
        """
        Transition to new status with validation

        Args:
            new_status: Target status

        Raises:
            ValueError: If transition is invalid
        """
        if not self.can_transition_to(new_status):
            raise ValueError(f"Invalid status transition: {self.status} → {new_status}")
        self.status = new_status
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entity to dictionary

        Returns:
            Dictionary representation
        """
        return {
            'id': str(self.id),
            'parent_project_id': str(self.parent_project_id),
            'organization_id': str(self.organization_id),
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'location_country': self.location_country,
            'location_region': self.location_region,
            'location_city': self.location_city,
            'location_address': self.location_address,
            'timezone': self.timezone,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'duration_weeks': self.duration_weeks,
            'max_participants': self.max_participants,
            'current_participants': self.current_participants,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'metadata': self.metadata,
            'capacity_percentage': round(self.calculate_capacity_percentage(), 2)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubProject':
        """
        Create entity from dictionary

        Args:
            data: Dictionary with entity data

        Returns:
            SubProject instance
        """
        # Convert string UUIDs to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'parent_project_id' in data and isinstance(data['parent_project_id'], str):
            data['parent_project_id'] = UUID(data['parent_project_id'])
        if 'organization_id' in data and isinstance(data['organization_id'], str):
            data['organization_id'] = UUID(data['organization_id'])
        if 'created_by' in data and data['created_by'] and isinstance(data['created_by'], str):
            data['created_by'] = UUID(data['created_by'])
        if 'updated_by' in data and data['updated_by'] and isinstance(data['updated_by'], str):
            data['updated_by'] = UUID(data['updated_by'])

        # Convert date strings to date objects
        if 'start_date' in data and isinstance(data['start_date'], str):
            data['start_date'] = date.fromisoformat(data['start_date'])
        if 'end_date' in data and isinstance(data['end_date'], str):
            data['end_date'] = date.fromisoformat(data['end_date'])

        # Convert datetime strings to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])

        # Remove capacity_percentage if present (calculated field)
        data.pop('capacity_percentage', None)

        return cls(**data)

    def __repr__(self) -> str:
        """String representation"""
        return (f"SubProject(id={self.id}, name='{self.name}', "
                f"locations='{self.location_city}, {self.location_country}', "
                f"status='{self.status}', participants={self.current_participants}/{self.max_participants})")
