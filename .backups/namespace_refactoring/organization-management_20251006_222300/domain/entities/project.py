"""
Project Entity - Business Logic Core
Single Responsibility: Project domain object with business rules
Dependency Inversion: No dependencies on external frameworks
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from enum import Enum


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

@dataclass

class Project:
    """
    Project entity representing a training program within an organization
    """
    organization_id: UUID
    name: str
    slug: str
    id: Optional[UUID] = None
    description: Optional[str] = None
    objectives: List[str] = None
    target_roles: List[str] = None
    duration_weeks: Optional[int] = None
    max_participants: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    settings: Dict[str, Any] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.objectives is None:
            self.objectives = []
        if self.target_roles is None:
            self.target_roles = []
        if self.settings is None:
            self.settings = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def update_info(self, name: str = None, description: str = None,
                   objectives: List[str] = None, target_roles: List[str] = None,
                   duration_weeks: int = None, max_participants: int = None,
                   start_date: date = None, end_date: date = None,
                   settings: Dict[str, Any] = None) -> None:
        """Update project information"""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if objectives is not None:
            self.objectives = objectives
        if target_roles is not None:
            self.target_roles = target_roles
        if duration_weeks is not None:
            self.duration_weeks = duration_weeks
        if max_participants is not None:
            self.max_participants = max_participants
        if start_date is not None:
            self.start_date = start_date
        if end_date is not None:
            self.end_date = end_date
        if settings is not None:
            self.settings = settings
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate project"""
        if self.status == ProjectStatus.DRAFT:
            self.status = ProjectStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark project as completed"""
        if self.status == ProjectStatus.ACTIVE:
            self.status = ProjectStatus.COMPLETED
            self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive project"""
        self.status = ProjectStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def validate_slug(self) -> bool:
        """Validate slug format"""
        import re
        return bool(re.match(r'^[a-z0-9-]+$', self.slug))

    def validate_dates(self) -> bool:
        """Validate date constraints"""
        if self.start_date and self.end_date:
            return self.end_date > self.start_date
        return True

    def validate_duration(self) -> bool:
        """Validate duration constraints"""
        if self.duration_weeks is not None:
            return 1 <= self.duration_weeks <= 104
        return True

    def validate_participants(self) -> bool:
        """Validate max participants constraint"""
        if self.max_participants is not None:
            return self.max_participants >= 1
        return True

    def is_valid(self) -> bool:
        """Check if project data is valid"""
        return (
            bool(self.name and len(self.name.strip()) >= 2) and
            bool(self.slug and len(self.slug.strip()) >= 2) and
            self.validate_slug() and
            self.validate_dates() and
            self.validate_duration() and
            self.validate_participants()
        )

    def can_activate(self) -> bool:
        """Check if project can be activated"""
        return self.status == ProjectStatus.DRAFT and self.is_valid()

    def can_complete(self) -> bool:
        """Check if project can be completed"""
        return self.status == ProjectStatus.ACTIVE

    def is_active(self) -> bool:
        """Check if project is currently active"""
        return self.status == ProjectStatus.ACTIVE