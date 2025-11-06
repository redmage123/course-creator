"""
Meeting Room Integration Entities
Supports MS Teams and Zoom room creation and management
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime


class MeetingPlatform(Enum):
    """Supported meeting platforms"""
    TEAMS = "teams"
    ZOOM = "zoom"
    SLACK = "slack"


class RoomType(Enum):
    """Types of meeting rooms"""
    TRACK_ROOM = "track_room"        # Room for entire track
    INSTRUCTOR_ROOM = "instructor_room"  # Personal instructor room
    PROJECT_ROOM = "project_room"    # Room for entire project
    ORGANIZATION_ROOM = "organization_room"  # Organization-wide room

@dataclass

class MeetingRoom:
    """Meeting room entity with platform integration"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    platform: MeetingPlatform = MeetingPlatform.TEAMS
    room_type: RoomType = RoomType.TRACK_ROOM

    # Context associations
    organization_id: UUID = None
    project_id: Optional[UUID] = None
    track_id: Optional[UUID] = None
    instructor_id: Optional[UUID] = None

    # Platform-specific data
    external_room_id: Optional[str] = None  # Teams/Zoom room ID
    join_url: Optional[str] = None
    host_url: Optional[str] = None
    meeting_id: Optional[str] = None
    passcode: Optional[str] = None

    # Room settings
    settings: Dict = field(default_factory=dict)
    is_recurring: bool = True
    max_participants: Optional[int] = None

    # Metadata
    created_by: UUID = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    status: str = "active"  # active, inactive, deleted

    def __post_init__(self):
        """Set default settings based on room type"""
        if not self.settings:
            self.settings = self._get_default_settings()

    def _get_default_settings(self) -> Dict:
        """Get default settings based on room type and platform"""
        base_settings = {
            "auto_recording": False,
            "waiting_room": True,
            "mute_on_entry": True,
            "allow_screen_sharing": True
        }

        # Platform-specific defaults
        if self.platform == MeetingPlatform.TEAMS:
            base_settings.update({
                "lobby_bypass": "organization",
                "entry_announcement": False,
                "chat_enabled": True
            })
        elif self.platform == MeetingPlatform.ZOOM:
            base_settings.update({
                "waiting_room": True,
                "join_before_host": False,
                "registration_required": False
            })

        # Room type-specific defaults
        if self.room_type == RoomType.INSTRUCTOR_ROOM:
            base_settings.update({
                "auto_recording": True,
                "max_participants": 50
            })
        elif self.room_type == RoomType.TRACK_ROOM:
            base_settings.update({
                "max_participants": 100,
                "breakout_rooms_enabled": True
            })

        return base_settings

    def get_display_name(self) -> str:
        """Generate display name for the room"""
        if self.name:
            return self.name

        # Generate based on context
        if self.room_type == RoomType.INSTRUCTOR_ROOM and self.instructor_id:
            return f"Instructor Room - {self.instructor_id}"
        elif self.room_type == RoomType.TRACK_ROOM and self.track_id:
            return f"Track Room - {self.track_id}"
        elif self.room_type == RoomType.PROJECT_ROOM and self.project_id:
            return f"Project Room - {self.project_id}"
        elif self.room_type == RoomType.ORGANIZATION_ROOM:
            return f"Organization Room - {self.organization_id}"

        return f"{self.room_type.value} - {self.id}"

    def is_accessible_by_user(self, user_id: UUID, user_role: 'EnhancedRole') -> bool:
        """Check if user can access this room"""
        from enhanced_role import RoleType, Permission

        # Site admins can access all rooms
        if user_role.role_type == RoleType.SITE_ADMIN:
            return True

        # Organization admins can access all org rooms
        if (user_role.role_type == RoleType.ORGANIZATION_ADMIN and
            user_role.organization_id == self.organization_id):
            return True

        # Instructor personal rooms
        if (self.room_type == RoomType.INSTRUCTOR_ROOM and
            self.instructor_id == user_id):
            return True

        # Track rooms - instructors assigned to track
        if (self.room_type == RoomType.TRACK_ROOM and
            user_role.can_teach_track(self.track_id)):
            return True

        # Track rooms - students assigned to track
        if (self.room_type == RoomType.TRACK_ROOM and
            user_role.can_access_track(self.track_id)):
            return True

        # Project rooms - users with project access
        if (self.room_type == RoomType.PROJECT_ROOM and
            user_role.can_manage_project(self.project_id)):
            return True

        return False

    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def deactivate(self):
        """Deactivate the room"""
        self.status = "inactive"
        self.updated_at = datetime.utcnow()

    def delete(self):
        """Mark room as deleted"""
        self.status = "deleted"
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if room is active"""
        return self.status == "active"

    def is_valid(self) -> bool:
        """Validate room configuration"""
        if not self.organization_id:
            return False

        # Room type specific validation
        if self.room_type == RoomType.TRACK_ROOM and not self.track_id:
            return False
        elif self.room_type == RoomType.INSTRUCTOR_ROOM and not self.instructor_id:
            return False
        elif self.room_type == RoomType.PROJECT_ROOM and not self.project_id:
            return False

        return True

    def to_dict(self) -> Dict:
        """Convert room to dictionary representation"""
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.get_display_name(),
            "platform": self.platform.value,
            "room_type": self.room_type.value,
            "organization_id": str(self.organization_id),
            "project_id": str(self.project_id) if self.project_id else None,
            "track_id": str(self.track_id) if self.track_id else None,
            "instructor_id": str(self.instructor_id) if self.instructor_id else None,
            "external_room_id": self.external_room_id,
            "join_url": self.join_url,
            "host_url": self.host_url,
            "meeting_id": self.meeting_id,
            "passcode": self.passcode,
            "settings": self.settings,
            "is_recurring": self.is_recurring,
            "max_participants": self.max_participants,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "status": self.status
        }

@dataclass

class MeetingRoomUsage:
    """Track meeting room usage statistics"""
    id: UUID = field(default_factory=uuid4)
    room_id: UUID = None
    user_id: UUID = None
    joined_at: datetime = field(default_factory=datetime.utcnow)
    left_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    def calculate_duration(self):
        """
        Calculate meeting room session duration in minutes

        BUSINESS PURPOSE:
        Tracks time spent in meeting rooms for usage analytics and billing.
        Helps organizations understand engagement patterns.

        WHY THIS APPROACH:
        - Only calculates if left_at is set (session ended)
        - Rounds to integer minutes for simplicity
        - Stores result for quick queries (denormalized data)

        BUSINESS ANALYTICS:
        Duration data used for:
        - Instructor engagement metrics
        - Student participation tracking
        - Resource utilization reports

        Returns:
            None - updates entity in place (sets duration_minutes)
        """
        if self.left_at:
            duration = self.left_at - self.joined_at
            self.duration_minutes = int(duration.total_seconds() / 60)

    def end_session(self):
        """
        End meeting room session and calculate duration

        BUSINESS PURPOSE:
        Records when user left meeting room and automatically calculates
        session duration for analytics.

        WHY THIS APPROACH:
        - Sets left_at to current time
        - Delegates duration calculation to calculate_duration()
        - Atomic operation ensures data consistency

        USAGE:
        Called when user disconnects from meeting room or closes browser.
        Can also be called by cleanup job for stale sessions.

        Returns:
            None - updates entity in place (sets left_at and duration_minutes)
        """
        self.left_at = datetime.utcnow()
        self.calculate_duration()

@dataclass

class MeetingRoomInvitation:
    """Meeting room access invitation"""
    id: UUID = field(default_factory=uuid4)
    room_id: UUID = None
    invitee_email: str = ""
    invitee_user_id: Optional[UUID] = None
    invited_by: UUID = None
    invited_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    access_level: str = "participant"  # host, co-host, participant
    status: str = "pending"  # pending, accepted, expired

    def accept(self):
        """
        Accept meeting room invitation

        BUSINESS PURPOSE:
        Records user acceptance of meeting room invitation and grants access.
        Transitions invitation from pending to accepted state.

        WHY THIS APPROACH:
        - Status change enables access to meeting room
        - Preserves invitation record for audit trail
        - Permanent acceptance (no expiration after acceptance)

        Returns:
            None - updates entity in place (sets status to "accepted")
        """
        self.status = "accepted"

    def expire(self):
        """
        Mark invitation as expired

        BUSINESS PURPOSE:
        Automatically expires invitations past their expiration date.
        Prevents access to meeting rooms with outdated invitations.

        WHY THIS APPROACH:
        - Status change prevents further acceptance
        - Preserves invitation record for audit trail
        - Called automatically by is_valid() check

        BUSINESS RULE:
        Expired invitations cannot be accepted. User must request new invitation.

        Returns:
            None - updates entity in place (sets status to "expired")
        """
        self.status = "expired"

    def is_valid(self) -> bool:
        """
        Check if invitation is still valid for acceptance

        BUSINESS PURPOSE:
        Validates invitation before granting meeting room access.
        Ensures invitations are pending and not expired.

        WHY THIS APPROACH:
        - Status check ensures invitation is pending (not already accepted or expired)
        - Expiration check automatically expires outdated invitations
        - Returns boolean for permission checks

        VALIDATION RULES:
        - Status must be "pending" (not "accepted" or "expired")
        - Current time must be before expires_at (if set)
        - Automatically expires invitation if past expiration

        Returns:
            bool: True if invitation is valid, False otherwise
        """
        if self.status != "pending":
            return False

        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.expire()
            return False

        return True