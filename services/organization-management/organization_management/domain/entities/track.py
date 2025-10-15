"""
Track Entity - Learning Path Business Logic Core
Single Responsibility: Track domain object with enrollment and progression rules
Dependency Inversion: No dependencies on external frameworks
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from enum import Enum


class TrackStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TrackType(str, Enum):
    SEQUENTIAL = "sequential"      # Students must complete classes in order
    FLEXIBLE = "flexible"          # Students can take classes in any order
    MILESTONE_BASED = "milestone_based"  # Based on milestone achievements


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class Track:
    """
    Track entity representing a learning path within a project or sub-project

    BUSINESS PURPOSE:
    Tracks organize courses into structured learning paths. They can belong to either
    a main project OR a sub-project (XOR constraint enforced at database level).

    EXAMPLES:
    - App Developer Track
    - Business Analyst Track
    - Operations Engineer Track

    FLEXIBLE HIERARCHY:
    - Track → Main Project (project_id set, sub_project_id NULL)
    - Track → Sub-Project → Main Project (sub_project_id set, project_id NULL)
    """
    organization_id: UUID           # Required for multi-tenancy
    name: str                       # Display name
    slug: str                       # URL-safe identifier
    id: Optional[UUID] = None

    # Flexible parent reference (XOR: project_id OR sub_project_id, not both)
    project_id: Optional[UUID] = None       # If track belongs to main project
    sub_project_id: Optional[UUID] = None   # If track belongs to sub-project

    description: Optional[str] = None
    track_type: TrackType = TrackType.SEQUENTIAL
    target_audience: List[str] = None  # ['Application Developer', 'Junior Developer']
    prerequisites: List[str] = None    # ['Basic Programming', 'Git Knowledge']
    duration_weeks: Optional[int] = None
    max_enrolled: Optional[int] = None
    learning_objectives: List[str] = None
    skills_taught: List[str] = None   # ['React', 'Node.js', 'Docker']
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    estimated_hours: Optional[int] = None  # Estimated completion time in hours
    display_order: int = 0           # Order within parent project/sub-project
    auto_enroll_enabled: bool = True  # Automatic enrollment when student joins project
    status: TrackStatus = TrackStatus.DRAFT
    settings: Dict[str, Any] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.target_audience is None:
            self.target_audience = []
        if self.prerequisites is None:
            self.prerequisites = []
        if self.learning_objectives is None:
            self.learning_objectives = []
        if self.skills_taught is None:
            self.skills_taught = []
        if self.settings is None:
            self.settings = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def update_info(self, name: str = None, description: str = None,
                   track_type: TrackType = None, target_audience: List[str] = None,
                   prerequisites: List[str] = None, duration_weeks: int = None,
                   max_enrolled: int = None, learning_objectives: List[str] = None,
                   skills_taught: List[str] = None, difficulty_level: str = None,
                   auto_enroll_enabled: bool = None, settings: Dict[str, Any] = None) -> None:
        """Update track information"""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if track_type is not None:
            self.track_type = track_type
        if target_audience is not None:
            self.target_audience = target_audience
        if prerequisites is not None:
            self.prerequisites = prerequisites
        if duration_weeks is not None:
            self.duration_weeks = duration_weeks
        if max_enrolled is not None:
            self.max_enrolled = max_enrolled
        if learning_objectives is not None:
            self.learning_objectives = learning_objectives
        if skills_taught is not None:
            self.skills_taught = skills_taught
        if difficulty_level is not None:
            self.difficulty_level = difficulty_level
        if auto_enroll_enabled is not None:
            self.auto_enroll_enabled = auto_enroll_enabled
        if settings is not None:
            self.settings = settings
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate track for student enrollment"""
        if self.status == TrackStatus.DRAFT and self.is_valid():
            self.status = TrackStatus.ACTIVE
            self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark track as completed"""
        if self.status == TrackStatus.ACTIVE:
            self.status = TrackStatus.COMPLETED
            self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive track"""
        self.status = TrackStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def validate_slug(self) -> bool:
        """Validate slug format"""
        import re
        return bool(re.match(r'^[a-z0-9-]+$', self.slug))

    def validate_duration(self) -> bool:
        """Validate duration constraints"""
        if self.duration_weeks is not None:
            return 1 <= self.duration_weeks <= 52
        return True

    def validate_enrollment_limit(self) -> bool:
        """Validate max enrollment constraint"""
        if self.max_enrolled is not None:
            return self.max_enrolled >= 1
        return True

    def validate_difficulty_level(self) -> bool:
        """Validate difficulty level"""
        valid_levels = ["beginner", "intermediate", "advanced"]
        return self.difficulty_level in valid_levels

    def validate_parent_reference(self) -> bool:
        """
        Validate XOR constraint: Track must reference EITHER project OR sub-project

        BUSINESS RULE:
        A track can belong to a main project OR a sub-project, but not both
        and not neither. This is enforced at the database level but we also
        validate it at the domain level for early error detection.

        Returns:
            bool: True if exactly one parent reference is set, False otherwise
        """
        has_project = self.project_id is not None
        has_subproject = self.sub_project_id is not None

        # XOR: exactly one must be True
        return (has_project and not has_subproject) or (not has_project and has_subproject)

    def is_valid(self) -> bool:
        """Check if track data is valid"""
        return (
            bool(self.name and len(self.name.strip()) >= 2) and
            bool(self.slug and len(self.slug.strip()) >= 2) and
            self.validate_slug() and
            self.validate_duration() and
            self.validate_enrollment_limit() and
            self.validate_difficulty_level() and
            self.validate_parent_reference()  # XOR constraint validation
        )

    def can_activate(self) -> bool:
        """Check if track can be activated"""
        return self.status == TrackStatus.DRAFT and self.is_valid()

    def can_enroll_students(self) -> bool:
        """Check if track accepts new student enrollments"""
        return self.status == TrackStatus.ACTIVE and self.auto_enroll_enabled

    def is_active(self) -> bool:
        """Check if track is currently active"""
        return self.status == TrackStatus.ACTIVE

    def get_target_audience_display(self) -> str:
        """Get formatted target audience string"""
        if not self.target_audience:
            return "General"
        return ", ".join(self.target_audience)

    def get_skills_display(self) -> str:
        """Get formatted skills string"""
        if not self.skills_taught:
            return "Various Skills"
        return ", ".join(self.skills_taught)

    def estimate_completion_time(self) -> str:
        """Estimate completion time based on duration and difficulty"""
        if not self.duration_weeks:
            return "Variable"

        base_weeks = self.duration_weeks

        # Adjust based on difficulty
        if self.difficulty_level == "advanced":
            base_weeks = int(base_weeks * 1.2)
        elif self.difficulty_level == "beginner":
            base_weeks = int(base_weeks * 0.9)

        if base_weeks == 1:
            return "1 week"
        elif base_weeks < 4:
            return f"{base_weeks} weeks"
        else:
            months = base_weeks // 4
            remaining_weeks = base_weeks % 4
            if remaining_weeks == 0:
                return f"{months} month{'s' if months > 1 else ''}"
            else:
                return f"{months} month{'s' if months > 1 else ''}, {remaining_weeks} week{'s' if remaining_weeks > 1 else ''}"


@dataclass
class TrackInstructor:
    """
    Track Instructor Assignment Entity

    BUSINESS PURPOSE:
    Represents the assignment of an instructor to a track with communication
    links for student-instructor interaction (Zoom, Teams, Slack).

    BUSINESS RULES:
    - One instructor can only be assigned once per track (unique constraint)
    - Minimum 1 instructor per track (enforced via database trigger)
    - Communication links are optional but recommended

    USAGE:
    Org admins assign instructors to tracks. Students assigned to the track
    will be distributed among the instructors (load balancing).
    """
    track_id: UUID              # Track this instructor teaches
    user_id: UUID               # Instructor user ID
    id: Optional[UUID] = None

    # Communication links for student-instructor interaction
    zoom_link: Optional[str] = None         # Office hours, lectures
    teams_link: Optional[str] = None        # Microsoft Teams meetings
    slack_links: List[str] = None           # Slack channels or DMs

    # Assignment metadata
    assigned_at: Optional[datetime] = None
    assigned_by: Optional[UUID] = None      # Org admin who made assignment

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.slack_links is None:
            self.slack_links = []
        if self.assigned_at is None:
            self.assigned_at = datetime.utcnow()

    def has_communication_links(self) -> bool:
        """Check if instructor has at least one communication link"""
        return bool(
            self.zoom_link or
            self.teams_link or
            (self.slack_links and len(self.slack_links) > 0)
        )

    def add_slack_link(self, slack_link: str) -> None:
        """Add a Slack channel or DM link"""
        if slack_link and slack_link not in self.slack_links:
            self.slack_links.append(slack_link)

    def remove_slack_link(self, slack_link: str) -> None:
        """Remove a Slack channel or DM link"""
        if slack_link in self.slack_links:
            self.slack_links.remove(slack_link)

    def update_communication_links(
        self,
        zoom_link: Optional[str] = None,
        teams_link: Optional[str] = None,
        slack_links: Optional[List[str]] = None
    ) -> None:
        """Update instructor communication links"""
        if zoom_link is not None:
            self.zoom_link = zoom_link
        if teams_link is not None:
            self.teams_link = teams_link
        if slack_links is not None:
            self.slack_links = slack_links


@dataclass
class TrackStudent:
    """
    Track Student Enrollment Entity

    BUSINESS PURPOSE:
    Represents the enrollment of a student in a track with optional instructor
    assignment for load balancing.

    BUSINESS RULES:
    - One student can only be enrolled once per track (unique constraint)
    - Student can be assigned to a specific instructor for that track
    - Assigned instructor must be teaching that track (enforced via database trigger)
    - Load balancing can automatically distribute students across instructors

    USAGE:
    Org admins enroll students in tracks. If auto-balance is enabled for the
    project/sub-project, students are automatically assigned to instructors
    with the lowest student count.
    """
    track_id: UUID              # Track the student is enrolled in
    student_id: UUID            # Student user ID
    id: Optional[UUID] = None

    # Instructor assignment for load balancing
    assigned_instructor_id: Optional[UUID] = None  # Which instructor teaches this student

    # Assignment metadata
    enrolled_at: Optional[datetime] = None
    assigned_by: Optional[UUID] = None             # Org admin who made assignment
    last_reassigned_at: Optional[datetime] = None  # Last reassignment timestamp

    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()
        if self.enrolled_at is None:
            self.enrolled_at = datetime.utcnow()

    def has_instructor(self) -> bool:
        """Check if student is assigned to an instructor"""
        return self.assigned_instructor_id is not None

    def assign_instructor(self, instructor_id: UUID, assigned_by: Optional[UUID] = None) -> None:
        """
        Assign student to a specific instructor

        BUSINESS LOGIC:
        Updates the assigned instructor and records the reassignment timestamp
        for audit trail purposes.
        """
        self.assigned_instructor_id = instructor_id
        self.last_reassigned_at = datetime.utcnow()
        if assigned_by is not None:
            self.assigned_by = assigned_by

    def unassign_instructor(self) -> None:
        """Remove instructor assignment (not recommended but allowed)"""
        self.assigned_instructor_id = None
        self.last_reassigned_at = datetime.utcnow()