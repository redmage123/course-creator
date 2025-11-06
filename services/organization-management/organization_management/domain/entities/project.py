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
    """
    Project lifecycle status enumeration

    BUSINESS PURPOSE:
    Tracks the current state of a training project through its lifecycle.
    Status transitions follow a specific workflow to ensure data integrity.

    STATUS WORKFLOW:
    DRAFT → ACTIVE → COMPLETED → ARCHIVED

    DRAFT: Project being configured, not visible to students
    ACTIVE: Project accepting enrollments and in progress
    COMPLETED: Project finished, no new enrollments
    ARCHIVED: Project completed and archived for historical reference
    """
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

@dataclass
class Project:
    """
    Project entity representing a training program within an organization

    BUSINESS PURPOSE:
    Projects are the top-level organizational unit for training programs.
    Each project contains tracks (learning paths) and enrolls students.

    EXAMPLES:
    - "Q4 2024 Developer Onboarding" - 12-week program for new hires
    - "AWS Certification Bootcamp" - 8-week certification preparation
    - "Leadership Development Program" - 16-week management training

    MULTI-TENANT CONSIDERATION:
    Each project belongs to exactly one organization. Projects are completely
    isolated between organizations - no cross-organization visibility or access.

    Attributes:
        organization_id: Parent organization UUID (required)
        name: Project display name
        slug: URL-safe identifier
        id: Unique project identifier (UUID)
        description: Project description/overview
        objectives: List of learning objectives
        target_roles: List of target job roles (e.g., ['Developer', 'Engineer'])
        duration_weeks: Expected project duration in weeks
        max_participants: Maximum student enrollment limit
        start_date: Project start date
        end_date: Project end date
        status: Current project status (DRAFT, ACTIVE, COMPLETED, ARCHIVED)
        settings: Custom project settings dictionary
        created_by: User UUID who created project
        created_at: Project creation timestamp (UTC)
        updated_at: Last modification timestamp (UTC)
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
        """
        Initialize project entity with default values

        BUSINESS PURPOSE:
        Ensures all projects have unique identifiers, timestamps, and default
        collections to prevent null reference errors.

        WHY THIS APPROACH:
        - UUID generation ensures globally unique project identifiers
        - Empty lists for objectives and target_roles allow optional configuration
        - Empty settings dict allows flexible configuration without schema changes
        - UTC timestamps provide timezone-independent record keeping

        TECHNICAL IMPLEMENTATION:
        Called automatically after dataclass initialization to set computed fields.
        """
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
        """
        Update project information

        BUSINESS PURPOSE:
        Allows organization admins to modify project details after creation.
        Supports partial updates without overwriting unchanged fields.

        WHY THIS APPROACH:
        - Optional parameters allow partial updates
        - updated_at timestamp tracks last modification for audit trail
        - List fields can be completely replaced (not appended)

        MULTI-TENANT CONSIDERATION:
        Only organization admins from the same organization can update projects.
        Cross-organization modifications are prevented at service layer.

        Args:
            name: Project display name
            description: Project description/overview
            objectives: List of learning objectives (replaces existing)
            target_roles: List of target job roles (replaces existing)
            duration_weeks: Expected project duration in weeks (1-104)
            max_participants: Maximum student enrollment limit (1+)
            start_date: Project start date
            end_date: Project end date (must be after start_date)
            settings: Custom project settings dictionary (replaces existing)

        Returns:
            None - updates entity in place
        """
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
        """
        Activate project to allow student enrollments

        BUSINESS PURPOSE:
        Transitions project from DRAFT to ACTIVE status, making it visible to
        students and enabling track enrollments.

        WHY THIS APPROACH:
        - Status check prevents activating already-active projects
        - Only DRAFT projects can be activated (workflow enforcement)
        - Updated timestamp tracks activation time for analytics

        BUSINESS RULE:
        Project must pass validation (is_valid()) before activation.
        Use can_activate() to check if activation is allowed.

        Returns:
            None - updates entity in place
        """
        if self.status == ProjectStatus.DRAFT:
            self.status = ProjectStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """
        Mark project as completed

        BUSINESS PURPOSE:
        Transitions project from ACTIVE to COMPLETED status when training program
        ends. Prevents new enrollments but preserves access for enrolled students.

        WHY THIS APPROACH:
        - Status check prevents completing non-active projects
        - Only ACTIVE projects can be completed (workflow enforcement)
        - Updated timestamp tracks completion time for analytics

        BUSINESS RULE:
        Enrolled students retain access to completed projects for certificate
        generation and review. No new enrollments accepted.

        Returns:
            None - updates entity in place
        """
        if self.status == ProjectStatus.ACTIVE:
            self.status = ProjectStatus.COMPLETED
            self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """
        Archive project for historical reference

        BUSINESS PURPOSE:
        Transitions project to ARCHIVED status for long-term storage.
        Archived projects are read-only and hidden from active project lists.

        WHY THIS APPROACH:
        - No status check - any project can be archived
        - Preserves data for compliance and historical analysis
        - Updated timestamp tracks archival time

        BUSINESS RULE:
        Archived projects cannot be modified. Students lose access.
        Use for outdated programs or after data retention period.

        Returns:
            None - updates entity in place
        """
        self.status = ProjectStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def validate_slug(self) -> bool:
        """
        Validate slug format follows URL-safe naming convention

        BUSINESS PURPOSE:
        Project slugs are used in URLs for project-specific pages
        (e.g., platform.com/projects/aws-bootcamp). Validation ensures URL compatibility.

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

    def validate_dates(self) -> bool:
        """
        Validate date constraints for project timeline

        BUSINESS PURPOSE:
        Ensures project end date is after start date to prevent invalid timelines.
        Critical for enrollment scheduling and progress tracking.

        WHY THIS APPROACH:
        - Optional dates return True (dates not required)
        - Both dates must be present for validation
        - End date must be strictly after start date (not equal)

        Args:
            None - validates self.start_date and self.end_date

        Returns:
            bool: True if dates are valid or absent, False if end <= start
        """
        if self.start_date and self.end_date:
            return self.end_date > self.start_date
        return True

    def validate_duration(self) -> bool:
        """
        Validate duration constraints

        BUSINESS PURPOSE:
        Ensures project duration is reasonable (1 week to 2 years).
        Prevents data entry errors and unrealistic project timelines.

        WHY THIS APPROACH:
        - Optional duration returns True (not required)
        - 1 week minimum prevents zero or negative durations
        - 104 weeks maximum (2 years) is typical maximum program length

        BUSINESS CONSTRAINT:
        Longer programs should be split into multiple projects for better
        tracking and student engagement.

        Args:
            None - validates self.duration_weeks

        Returns:
            bool: True if duration is 1-104 weeks or absent, False otherwise
        """
        if self.duration_weeks is not None:
            return 1 <= self.duration_weeks <= 104
        return True

    def validate_participants(self) -> bool:
        """
        Validate max participants constraint

        BUSINESS PURPOSE:
        Ensures enrollment limit is positive. Prevents configuration errors
        that would block all enrollments.

        WHY THIS APPROACH:
        - Optional limit returns True (unlimited enrollment)
        - Minimum 1 participant allows at least one enrollment
        - No maximum limit - organizations can set any reasonable value

        Args:
            None - validates self.max_participants

        Returns:
            bool: True if max_participants >= 1 or absent, False otherwise
        """
        if self.max_participants is not None:
            return self.max_participants >= 1
        return True

    def is_valid(self) -> bool:
        """
        Check if project data is valid for activation

        BUSINESS PURPOSE:
        Comprehensive validation before project activation. Ensures all
        required fields are present and constraints are met.

        WHY THIS APPROACH:
        - Combines multiple validators for complete validation
        - Name and slug minimum 2 chars prevents empty values
        - Delegates to specific validators for separation of concerns

        VALIDATION RULES:
        - Name: minimum 2 characters, non-empty
        - Slug: minimum 2 characters, URL-safe format
        - Dates: end_date after start_date (if present)
        - Duration: 1-104 weeks (if present)
        - Participants: minimum 1 (if present)

        Args:
            None - validates entire entity

        Returns:
            bool: True if all validations pass, False otherwise
        """
        return (
            bool(self.name and len(self.name.strip()) >= 2) and
            bool(self.slug and len(self.slug.strip()) >= 2) and
            self.validate_slug() and
            self.validate_dates() and
            self.validate_duration() and
            self.validate_participants()
        )

    def can_activate(self) -> bool:
        """
        Check if project can be activated

        BUSINESS PURPOSE:
        Determines if project meets requirements for activation.
        Used by UI to enable/disable activation button.

        WHY THIS APPROACH:
        - Combines status check and validation
        - Only DRAFT projects can be activated
        - Validation ensures project is properly configured

        Args:
            None

        Returns:
            bool: True if project is DRAFT and valid, False otherwise
        """
        return self.status == ProjectStatus.DRAFT and self.is_valid()

    def can_complete(self) -> bool:
        """
        Check if project can be completed

        BUSINESS PURPOSE:
        Determines if project can transition to COMPLETED status.
        Used by UI to enable/disable completion button.

        WHY THIS APPROACH:
        - Only ACTIVE projects can be completed (workflow enforcement)
        - Prevents marking DRAFT projects as complete

        Args:
            None

        Returns:
            bool: True if project is ACTIVE, False otherwise
        """
        return self.status == ProjectStatus.ACTIVE

    def is_active(self) -> bool:
        """
        Check if project is currently active

        BUSINESS PURPOSE:
        Quick status check for determining if project accepts enrollments.
        Used throughout application for permission checks.

        WHY THIS APPROACH:
        - Simple boolean for readability (self.is_active() vs self.status == ProjectStatus.ACTIVE)
        - Encapsulates status check logic

        Args:
            None

        Returns:
            bool: True if project status is ACTIVE, False otherwise
        """
        return self.status == ProjectStatus.ACTIVE