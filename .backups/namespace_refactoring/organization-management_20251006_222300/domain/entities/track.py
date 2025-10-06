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
    Track entity representing a learning path within a project
    Examples: App Developer Track, Business Analyst Track, Operations Engineer Track
    """
    project_id: UUID
    name: str
    slug: str
    id: Optional[UUID] = None
    description: Optional[str] = None
    track_type: TrackType = TrackType.SEQUENTIAL
    target_audience: List[str] = None  # ['Application Developer', 'Junior Developer']
    prerequisites: List[str] = None    # ['Basic Programming', 'Git Knowledge']
    duration_weeks: Optional[int] = None
    max_enrolled: Optional[int] = None
    learning_objectives: List[str] = None
    skills_taught: List[str] = None   # ['React', 'Node.js', 'Docker']
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    sequence_order: int = 0           # Order within project
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

    def is_valid(self) -> bool:
        """Check if track data is valid"""
        return (
            bool(self.name and len(self.name.strip()) >= 2) and
            bool(self.slug and len(self.slug.strip()) >= 2) and
            self.validate_slug() and
            self.validate_duration() and
            self.validate_enrollment_limit() and
            self.validate_difficulty_level()
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